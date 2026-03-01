"""
Detector de oportunidades de hedge entre Binance y Polymarket.

Logica principal:
  1. Tenemos señal tecnica de Binance (direction + confidence)
  2. Miramos mercados de Polymarket: "Will BTC be above $X on date Y?"
  3. Calculamos probabilidad "justa" basada en precio actual vs strike + tiempo
  4. Si Polymarket muestra una probabilidad significativamente diferente → OPORTUNIDAD
  5. Entramos comprando el lado correcto (YES si creemos que sube, NO si baja)
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from math import log, sqrt, exp
from scipy.stats import norm

from config import cfg
from src.analysis.predictor import MTFSignal
from src.logger import setup_logger
from src.polymarket.client import Market

log = setup_logger("hedge_detector")


@dataclass
class HedgeOpportunity:
    market: Market
    signal: MTFSignal
    # Token que compramos (YES o NO token_id)
    token_id: str
    outcome_label: str          # "YES" o "NO"
    side: str                   # "BUY"
    # Precios
    market_price: float         # probabilidad actual en Polymarket
    fair_price: float           # nuestra estimacion de la probabilidad real
    edge: float                 # fair_price - market_price (positivo = queremos BUY)
    # Metricas
    confidence: float
    expected_value: float       # EV por USDC apostado
    hours_to_expiry: float

    def __str__(self) -> str:
        return (
            f"HEDGE [{self.market.crypto_symbol}] "
            f"{self.outcome_label}@{self.market_price:.3f} → fair={self.fair_price:.3f} "
            f"edge={self.edge:+.3f} EV={self.expected_value:.3f} "
            f"conf={self.confidence:.2f} exp={self.hours_to_expiry:.1f}h | "
            f"{self.market.question[:60]}"
        )


class HedgeDetector:
    """
    Detecta discrepancias de precio entre Binance y Polymarket.
    """

    # Volatilidad historica implicita por defecto (annualizada)
    DEFAULT_VOL: dict = {
        "BTC": 0.70,
        "ETH": 0.90,
        "SOL": 1.20,
        "BNB": 0.85,
        "AVAX": 1.10,
    }

    def __init__(self, min_liquidity: float = 1000.0):
        self.min_liquidity = min_liquidity

    def find_opportunities(
        self,
        signal: MTFSignal,
        markets: List[Market],
    ) -> List[HedgeOpportunity]:
        """
        Dado un PriceSignal y lista de mercados activos,
        retorna lista de oportunidades ordenadas por expected value.
        """
        if not signal.is_actionable():
            return []

        opportunities = []

        for market in markets:
            if market.crypto_symbol != signal.symbol:
                continue
            if market.closed or not market.active:
                continue
            if market.liquidity < self.min_liquidity:
                log.debug(
                    f"Mercado {market.condition_id[:8]} ignorado: "
                    f"liquidez insuficiente {market.liquidity:.0f} < {self.min_liquidity}"
                )
                continue
            if not market.strike_price or not market.direction:
                continue

            opp = self._evaluate_market(signal, market)
            if opp and opp.edge >= cfg.MIN_EDGE_THRESHOLD:
                opportunities.append(opp)
                log.info(f"Oportunidad: {opp}")

        opportunities.sort(key=lambda o: o.expected_value, reverse=True)
        return opportunities

    def _evaluate_market(
        self, signal: MTFSignal, market: Market
    ) -> Optional[HedgeOpportunity]:
        """
        Evalua si hay oportunidad en un mercado concreto.
        Calcula probabilidad justa con modelo Black-Scholes simplificado.
        """
        hours_to_expiry = self._hours_to_expiry(market.end_date_iso)
        if hours_to_expiry <= 0:
            return None
        if hours_to_expiry > 720:  # más de 30 días → señal tecnica no predice bien
            log.debug(f"Mercado demasiado lejano ({hours_to_expiry:.0f}h)")
            return None

        # Probabilidad "justa" de que el precio supere el strike
        fair_prob_above = self._black_scholes_prob(
            spot=signal.current_price,
            strike=market.strike_price,
            hours=hours_to_expiry,
            annual_vol=self.DEFAULT_VOL.get(signal.symbol, 0.85),
            drift_adjustment=self._drift_from_signal(signal),
        )

        # Identificar token YES y NO
        yes_token = next((t for t in market.tokens if t["outcome"].upper() == "YES"), None)
        no_token = next((t for t in market.tokens if t["outcome"].upper() == "NO"), None)

        if not yes_token or not no_token:
            return None

        yes_market_price = yes_token["price"]  # probabilidad que Polymarket asigna a YES

        # Segun la pregunta del mercado:
        #   "Will BTC be ABOVE $X?" → YES gana si BTC > X → fair=fair_prob_above
        #   "Will BTC be BELOW $X?" → YES gana si BTC < X → fair=1-fair_prob_above

        if market.direction == "above":
            fair_yes = fair_prob_above
        else:  # "below"
            fair_yes = 1.0 - fair_prob_above

        # Ajuste por confianza de la señal: suavizar hacia 0.5
        smoothed_fair_yes = 0.5 + (fair_yes - 0.5) * signal.confidence

        edge = smoothed_fair_yes - yes_market_price

        # Decidir que token comprar
        if edge > cfg.MIN_EDGE_THRESHOLD:
            # YES esta barato → comprar YES
            token_id = yes_token["token_id"]
            outcome_label = "YES"
            market_price = yes_market_price
            fair_price = smoothed_fair_yes
            buy_edge = edge
        elif -edge > cfg.MIN_EDGE_THRESHOLD:
            # YES esta caro → comprar NO (= vender YES indirectamente)
            no_market_price = no_token["price"]
            fair_no = 1.0 - smoothed_fair_yes
            no_edge = fair_no - no_market_price
            if no_edge < cfg.MIN_EDGE_THRESHOLD:
                return None
            token_id = no_token["token_id"]
            outcome_label = "NO"
            market_price = no_market_price
            fair_price = fair_no
            buy_edge = no_edge
        else:
            return None

        # Expected value por USDC apostado
        # Si acertamos: ganamos (1/market_price - 1) * stake
        # Si fallamos: perdemos stake
        ev = fair_price * (1.0 / market_price - 1.0) - (1.0 - fair_price)

        return HedgeOpportunity(
            market=market,
            signal=signal,
            token_id=token_id,
            outcome_label=outcome_label,
            side="BUY",
            market_price=market_price,
            fair_price=fair_price,
            edge=buy_edge,
            confidence=signal.confidence,
            expected_value=ev,
            hours_to_expiry=hours_to_expiry,
        )

    @staticmethod
    def _black_scholes_prob(
        spot: float,
        strike: float,
        hours: float,
        annual_vol: float,
        drift_adjustment: float = 0.0,
    ) -> float:
        """
        Probabilidad log-normal de que spot > strike en T horas.
        drift_adjustment: sesgo adicional del predictor (en unidades anuales).
        """
        T = hours / 8760  # años
        if T <= 0 or annual_vol <= 0:
            return 1.0 if spot > strike else 0.0

        drift = drift_adjustment  # puede ser positivo o negativo segun señal
        sigma_sqrt_T = annual_vol * sqrt(T)

        d2 = (log(spot / strike) + (drift - 0.5 * annual_vol ** 2) * T) / sigma_sqrt_T
        prob = float(norm.cdf(d2))
        return max(0.02, min(0.98, prob))  # clamp para evitar extremos

    @staticmethod
    def _drift_from_signal(signal: MTFSignal) -> float:
        """
        Convierte la señal MTF en un drift anualizado para el modelo B-S.

        Cuando 5m y 15m coinciden (lead-lag sobre Polymarket) el drift
        se amplifica: es exactamente la ventana donde el VPS de Lituania
        tiene ventaja de velocidad antes de que Polymarket corrija.
        """
        base = abs(signal.momentum) * signal.confidence * 8.0

        # Multiplicador por confluencia de TFs
        if signal.tfs_agree:
            # Ambos TF apuntan igual → maxima conviccion, drift mas agresivo
            multiplier = 1.5
        elif signal.signal_15m is None or signal.signal_15m.direction == "neutral":
            # Solo tenemos 5m o 15m neutral → drift moderado
            multiplier = 1.0
        else:
            # Discrepancia (no deberia llegar aqui porque direction="neutral")
            multiplier = 0.0

        drift = base * multiplier
        return drift if signal.direction == "up" else -drift

    @staticmethod
    def _hours_to_expiry(end_date_iso: str) -> float:
        if not end_date_iso:
            return -1.0
        try:
            # Intentar varios formatos
            for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"]:
                try:
                    end_dt = datetime.strptime(end_date_iso, fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue
            else:
                return -1.0
            now = datetime.now(timezone.utc)
            delta = (end_dt - now).total_seconds() / 3600
            return delta
        except Exception:
            return -1.0
