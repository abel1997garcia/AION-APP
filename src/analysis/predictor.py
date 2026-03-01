"""
Motor de prediccion de precio basado en analisis tecnico.
Usa datos de Binance WebSocket para generar señales direccionales.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from config import cfg
from src.logger import setup_logger
from src.price_feed import PriceFeed

log = setup_logger("predictor")


@dataclass
class PriceSignal:
    symbol: str
    current_price: float
    direction: str          # "up", "down", "neutral"
    confidence: float       # 0.0 - 1.0
    momentum: float         # % cambio en ventana
    rsi: Optional[float]
    ema_fast: Optional[float]
    ema_slow: Optional[float]
    ema_trend: str          # "bullish", "bearish", "neutral"
    price_velocity: float   # velocidad de cambio (precio/minuto)

    def is_actionable(self) -> bool:
        return (
            self.direction != "neutral"
            and self.confidence >= cfg.MIN_CONFIDENCE
            and abs(self.momentum) >= cfg.PRICE_MOVE_THRESHOLD
        )


class TechnicalPredictor:
    """
    Calcula señales tecnicas sobre el historico de velas de Binance.
    Genera PriceSignal con direccion y confianza.
    """

    def __init__(self, feed: PriceFeed):
        self.feed = feed

    def analyze(self, symbol: str) -> Optional[PriceSignal]:
        """
        Analiza el historico de un simbolo y retorna señal de precio.
        """
        closes = self.feed.get_last_n_closes(symbol, cfg.PRICE_HISTORY_LIMIT)
        if len(closes) < cfg.EMA_SLOW + 5:
            log.debug(f"[{symbol}] Insuficientes velas ({len(closes)}), esperando...")
            return None

        current_price = self.feed.get_price(symbol)
        if not current_price:
            return None

        closes_arr = np.array(closes, dtype=float)

        ema_fast = self._ema(closes_arr, cfg.EMA_FAST)
        ema_slow = self._ema(closes_arr, cfg.EMA_SLOW)
        rsi = self._rsi(closes_arr, cfg.RSI_PERIOD)
        momentum = self._momentum(closes_arr, cfg.MOMENTUM_WINDOW)
        velocity = self._price_velocity(closes_arr)

        ema_trend = self._classify_ema(ema_fast, ema_slow)
        direction, confidence = self._aggregate_signal(
            ema_trend=ema_trend,
            rsi=rsi,
            momentum=momentum,
            velocity=velocity,
        )

        signal = PriceSignal(
            symbol=symbol,
            current_price=current_price,
            direction=direction,
            confidence=confidence,
            momentum=momentum,
            rsi=rsi,
            ema_fast=ema_fast[-1] if ema_fast is not None else None,
            ema_slow=ema_slow[-1] if ema_slow is not None else None,
            ema_trend=ema_trend,
            price_velocity=velocity,
        )

        log.debug(
            f"[{symbol}] Señal: {direction} conf={confidence:.2f} "
            f"rsi={rsi:.1f} mom={momentum:.4f} vel={velocity:.4f}"
        )
        return signal

    # ------------------------------------------------------------------ #
    # Indicadores                                                          #
    # ------------------------------------------------------------------ #

    def _ema(self, data: np.ndarray, period: int) -> Optional[np.ndarray]:
        if len(data) < period:
            return None
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[period - 1] = data[:period].mean()
        for i in range(period, len(data)):
            ema[i] = data[i] * alpha + ema[i - 1] * (1 - alpha)
        return ema[period - 1:]

    def _rsi(self, data: np.ndarray, period: int) -> float:
        if len(data) < period + 1:
            return 50.0
        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = gains[-period:].mean()
        avg_loss = losses[-period:].mean()
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return float(100 - 100 / (1 + rs))

    def _momentum(self, data: np.ndarray, window: int) -> float:
        """Retorno porcentual en la ventana."""
        if len(data) < window + 1:
            return 0.0
        return float((data[-1] - data[-window - 1]) / data[-window - 1])

    def _price_velocity(self, data: np.ndarray, window: int = 5) -> float:
        """
        Pendiente lineal normalizada de los ultimos `window` cierres.
        Positivo = acelerando al alza, Negativo = a la baja.
        """
        if len(data) < window:
            return 0.0
        subset = data[-window:]
        x = np.arange(window)
        slope, _ = np.polyfit(x, subset, 1)
        # Normalizar por precio medio para hacerlo relativo
        return float(slope / subset.mean())

    def _classify_ema(
        self, ema_fast: Optional[np.ndarray], ema_slow: Optional[np.ndarray]
    ) -> str:
        if ema_fast is None or ema_slow is None:
            return "neutral"
        f, s = ema_fast[-1], ema_slow[-1]
        if f > s * 1.001:
            return "bullish"
        if f < s * 0.999:
            return "bearish"
        return "neutral"

    def _aggregate_signal(
        self,
        ema_trend: str,
        rsi: float,
        momentum: float,
        velocity: float,
    ) -> Tuple[str, float]:
        """
        Combina indicadores en una señal direccional y nivel de confianza.
        Cada indicador aporta puntos; la confianza es la fraccion de acuerdo.
        """
        bullish_score = 0.0
        bearish_score = 0.0

        # --- EMA trend (peso 0.35) ---
        if ema_trend == "bullish":
            bullish_score += 0.35
        elif ema_trend == "bearish":
            bearish_score += 0.35

        # --- RSI (peso 0.25) ---
        if rsi < 30:         # sobreventa → rebote probable
            bullish_score += 0.25
        elif rsi < 45:
            bullish_score += 0.10
        elif rsi > 70:       # sobrecompra → corrección probable
            bearish_score += 0.25
        elif rsi > 55:
            bearish_score += 0.10

        # --- Momentum (peso 0.25) ---
        if momentum > cfg.PRICE_MOVE_THRESHOLD:
            bullish_score += 0.25
        elif momentum > cfg.PRICE_MOVE_THRESHOLD * 0.5:
            bullish_score += 0.10
        elif momentum < -cfg.PRICE_MOVE_THRESHOLD:
            bearish_score += 0.25
        elif momentum < -cfg.PRICE_MOVE_THRESHOLD * 0.5:
            bearish_score += 0.10

        # --- Velocidad (peso 0.15) ---
        if velocity > 0.001:
            bullish_score += 0.15
        elif velocity < -0.001:
            bearish_score += 0.15

        total = bullish_score + bearish_score
        if total == 0:
            return "neutral", 0.0

        if bullish_score > bearish_score:
            confidence = bullish_score / (bullish_score + bearish_score)
            return "up", confidence
        elif bearish_score > bullish_score:
            confidence = bearish_score / (bullish_score + bearish_score)
            return "down", confidence
        else:
            return "neutral", 0.5
