"""
Motor de prediccion multi-timeframe (5m + 15m).

Estrategia MTF:
  - 15m → tendencia de fondo (EMA, RSI). Filtra la direccion macro.
  - 5m  → timing de entrada (momentum, velocidad). Dispara la señal.

Reglas de combinacion:
  - Ambos TF coinciden    → boost de confianza (+MTF_AGREEMENT_BOOST)
  - 15m neutral, 5m claro → señal moderada (penalizacion leve)
  - Ambos discrepan       → NO operar (direction="neutral")

Esto evita entrar en contra de la tendencia de 15m aunque el 5m muestre
un movimiento puntual, reduciendo falsos positivos.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from config import cfg
from src.logger import setup_logger
from src.price_feed import PriceFeed

log = setup_logger("predictor")


# ─────────────────────────────────────────────────────────────────────────────
# Estructuras de datos
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TFSignal:
    """Señal para un unico timeframe."""
    timeframe: str          # "5m" o "15m"
    direction: str          # "up", "down", "neutral"
    confidence: float       # 0.0 – 1.0
    momentum: float         # retorno % en la ventana del TF
    rsi: Optional[float]
    ema_fast: Optional[float]
    ema_slow: Optional[float]
    ema_trend: str          # "bullish", "bearish", "neutral"
    velocity: float         # pendiente normalizada de precio


@dataclass
class MTFSignal:
    """
    Señal combinada 5m + 15m.
    Interfaz compatible con lo que espera HedgeDetector:
      .symbol, .current_price, .direction, .confidence, .momentum, .is_actionable()
    """
    symbol: str
    current_price: float

    # Señal combinada (lo que usa HedgeDetector)
    direction: str          # "up", "down", "neutral"
    confidence: float       # 0.0 – 1.0 (combinado)
    momentum: float         # momentum del TF de entrada (5m)

    # Detalle por TF (para logging y debugging)
    signal_5m: Optional[TFSignal]
    signal_15m: Optional[TFSignal]
    tfs_agree: bool         # True si ambos TFs apuntan en la misma direccion

    def is_actionable(self) -> bool:
        return (
            self.direction != "neutral"
            and self.confidence >= cfg.MIN_CONFIDENCE
            and abs(self.momentum) >= cfg.PRICE_MOVE_THRESHOLD
        )

    def log_summary(self) -> str:
        s5 = self.signal_5m
        s15 = self.signal_15m
        tf5_str = (
            f"5m→{s5.direction}({s5.confidence:.2f}) RSI={s5.rsi:.1f} mom={s5.momentum:+.4f}"
            if s5 else "5m→N/A"
        )
        tf15_str = (
            f"15m→{s15.direction}({s15.confidence:.2f}) RSI={s15.rsi:.1f} mom={s15.momentum:+.4f}"
            if s15 else "15m→N/A"
        )
        agree = "ACUERDO✓" if self.tfs_agree else ("DISCREPAN✗" if s15 else "15m esperando")
        return (
            f"[{self.symbol}] ${self.current_price:,.2f} | "
            f"{tf5_str} | {tf15_str} | {agree} | "
            f"COMBINADO: {self.direction} conf={self.confidence:.2f}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Predictor
# ─────────────────────────────────────────────────────────────────────────────

class TechnicalPredictor:
    """
    Calcula señales tecnicas multi-timeframe sobre los datos de PriceFeed.
    """

    # Parametros por timeframe: (ema_fast, ema_slow, rsi_period, momentum_window)
    TF_PARAMS: Dict[str, Tuple[int, int, int, int]] = {
        "5m":  (cfg.EMA_FAST_5M,  cfg.EMA_SLOW_5M,  cfg.RSI_PERIOD_5M,  cfg.MOMENTUM_WINDOW_5M),
        "15m": (cfg.EMA_FAST_15M, cfg.EMA_SLOW_15M, cfg.RSI_PERIOD_15M, cfg.MOMENTUM_WINDOW_15M),
    }

    def __init__(self, feed: PriceFeed):
        self.feed = feed

    # ------------------------------------------------------------------ #
    # API publica                                                          #
    # ------------------------------------------------------------------ #

    def analyze_mtf(self, symbol: str) -> Optional[MTFSignal]:
        """
        Analiza 5m y 15m y retorna señal combinada.
        Retorna None si no hay suficientes datos de 5m (TF de entrada).
        """
        current_price = self.feed.get_price(symbol)
        if not current_price:
            return None

        sig_5m = self._analyze_tf(symbol, cfg.TF_ENTRY)
        sig_15m = self._analyze_tf(symbol, cfg.TF_TREND)

        if sig_5m is None:
            # Sin datos de entrada → imposible operar
            counts = self.feed.candle_counts(symbol)
            needed = cfg.EMA_SLOW_5M + 5
            log.debug(
                f"[{symbol}] Esperando velas 5m: {counts.get('5m', 0)}/{needed}"
            )
            return None

        return self._combine(symbol, current_price, sig_5m, sig_15m)

    # ------------------------------------------------------------------ #
    # Analisis por timeframe                                               #
    # ------------------------------------------------------------------ #

    def _analyze_tf(self, symbol: str, timeframe: str) -> Optional[TFSignal]:
        ema_fast_p, ema_slow_p, rsi_p, mom_w = self.TF_PARAMS[timeframe]
        closes = self.feed.get_last_n_closes(symbol, timeframe, cfg.PRICE_HISTORY_LIMIT)

        if len(closes) < ema_slow_p + 5:
            return None

        arr = np.array(closes, dtype=float)
        ema_fast = self._ema(arr, ema_fast_p)
        ema_slow = self._ema(arr, ema_slow_p)
        rsi = self._rsi(arr, rsi_p)
        momentum = self._momentum(arr, mom_w)
        velocity = self._velocity(arr)
        ema_trend = self._classify_ema(ema_fast, ema_slow)
        direction, confidence = self._score_signal(ema_trend, rsi, momentum, velocity, timeframe)

        return TFSignal(
            timeframe=timeframe,
            direction=direction,
            confidence=confidence,
            momentum=momentum,
            rsi=rsi,
            ema_fast=float(ema_fast[-1]) if ema_fast is not None else None,
            ema_slow=float(ema_slow[-1]) if ema_slow is not None else None,
            ema_trend=ema_trend,
            velocity=velocity,
        )

    # ------------------------------------------------------------------ #
    # Combinacion multi-timeframe                                          #
    # ------------------------------------------------------------------ #

    def _combine(
        self,
        symbol: str,
        current_price: float,
        sig_5m: TFSignal,
        sig_15m: Optional[TFSignal],
    ) -> MTFSignal:
        """
        Reglas de combinacion:
          1. 15m no disponible        → 5m con penalizacion (-0.15)
          2. 15m neutral              → 5m con leve penalizacion (-0.08)
          3. 5m y 15m coinciden       → boost de confianza (+MTF_AGREEMENT_BOOST)
          4. 5m y 15m discrepan       → direction=neutral (no operar)
        """
        if sig_15m is None:
            # Todavia acumulando velas de 15m
            direction = sig_5m.direction
            confidence = max(0.0, sig_5m.confidence - 0.15)
            tfs_agree = False

        elif sig_15m.direction == "neutral":
            # 15m sin tendencia clara, nos fiamos del 5m con descuento
            direction = sig_5m.direction
            confidence = max(0.0, sig_5m.confidence - 0.08)
            tfs_agree = False

        elif sig_5m.direction == sig_15m.direction:
            # Confluencia: ambos apuntan en la misma direccion → maxima confianza
            # Promedio ponderado (5m pesa 60%, 15m 40%) + boost
            raw = sig_5m.confidence * 0.60 + sig_15m.confidence * 0.40
            confidence = min(1.0, raw + cfg.MTF_AGREEMENT_BOOST)
            direction = sig_5m.direction
            tfs_agree = True

        else:
            # Discrepancia: 5m dice una cosa, 15m dice la contraria → abstenerse
            confidence = 0.0
            direction = "neutral"
            tfs_agree = False

        return MTFSignal(
            symbol=symbol,
            current_price=current_price,
            direction=direction,
            confidence=confidence,
            momentum=sig_5m.momentum,  # timing de entrada siempre desde 5m
            signal_5m=sig_5m,
            signal_15m=sig_15m,
            tfs_agree=tfs_agree,
        )

    # ------------------------------------------------------------------ #
    # Indicadores tecnicos                                                 #
    # ------------------------------------------------------------------ #

    def _ema(self, data: np.ndarray, period: int) -> Optional[np.ndarray]:
        if len(data) < period:
            return None
        alpha = 2.0 / (period + 1)
        ema = np.empty(len(data))
        ema[period - 1] = data[:period].mean()
        for i in range(period, len(data)):
            ema[i] = data[i] * alpha + ema[i - 1] * (1 - alpha)
        return ema[period - 1:]

    def _rsi(self, data: np.ndarray, period: int) -> float:
        if len(data) < period + 1:
            return 50.0
        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = gains[-period:].mean()
        avg_loss = losses[-period:].mean()
        if avg_loss == 0:
            return 100.0
        return float(100 - 100 / (1 + avg_gain / avg_loss))

    def _momentum(self, data: np.ndarray, window: int) -> float:
        if len(data) < window + 1:
            return 0.0
        return float((data[-1] - data[-window - 1]) / data[-window - 1])

    def _velocity(self, data: np.ndarray, window: int = 4) -> float:
        """Pendiente lineal normalizada de los ultimos `window` cierres."""
        if len(data) < window:
            return 0.0
        subset = data[-window:]
        slope, _ = np.polyfit(np.arange(window), subset, 1)
        return float(slope / subset.mean())

    def _classify_ema(
        self,
        ema_fast: Optional[np.ndarray],
        ema_slow: Optional[np.ndarray],
    ) -> str:
        if ema_fast is None or ema_slow is None:
            return "neutral"
        f, s = ema_fast[-1], ema_slow[-1]
        if f > s * 1.0008:
            return "bullish"
        if f < s * 0.9992:
            return "bearish"
        return "neutral"

    def _score_signal(
        self,
        ema_trend: str,
        rsi: float,
        momentum: float,
        velocity: float,
        timeframe: str,
    ) -> Tuple[str, float]:
        """
        Puntua indicadores en alcista/bajista y calcula confianza.
        Los pesos estan ajustados por timeframe:
          - 5m: el momentum y la velocidad pesan mas (timing)
          - 15m: la tendencia EMA pesa mas (contexto)
        """
        bull = 0.0
        bear = 0.0

        if timeframe == cfg.TF_ENTRY:  # 5m
            w_ema, w_rsi, w_mom, w_vel = 0.25, 0.20, 0.35, 0.20
        else:  # 15m
            w_ema, w_rsi, w_mom, w_vel = 0.40, 0.25, 0.25, 0.10

        # EMA
        if ema_trend == "bullish":
            bull += w_ema
        elif ema_trend == "bearish":
            bear += w_ema

        # RSI
        if rsi < 30:
            bull += w_rsi
        elif rsi < 45:
            bull += w_rsi * 0.4
        elif rsi > 70:
            bear += w_rsi
        elif rsi > 55:
            bear += w_rsi * 0.4

        # Momentum
        thr = cfg.PRICE_MOVE_THRESHOLD
        if momentum > thr:
            bull += w_mom
        elif momentum > thr * 0.5:
            bull += w_mom * 0.4
        elif momentum < -thr:
            bear += w_mom
        elif momentum < -thr * 0.5:
            bear += w_mom * 0.4

        # Velocidad
        if velocity > 0.0008:
            bull += w_vel
        elif velocity < -0.0008:
            bear += w_vel

        total = bull + bear
        if total == 0:
            return "neutral", 0.0

        if bull > bear:
            return "up", bull / total
        if bear > bull:
            return "down", bear / total
        return "neutral", 0.5
