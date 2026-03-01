"""
Feed de precios en tiempo real via Binance WebSocket.
Suscribe a kline_5m + kline_15m + miniTicker por simbolo en un unico stream.
Mantiene historico de velas OHLCV separado por simbolo Y timeframe.
"""
import asyncio
import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import websockets

from config import cfg
from src.logger import setup_logger

log = setup_logger("price_feed")

# Timeframes que trackea el bot
TIMEFRAMES = (cfg.TF_ENTRY, cfg.TF_TREND)  # ("5m", "15m")


@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_closed: bool


@dataclass
class TickerData:
    symbol: str
    price: float
    timestamp: datetime
    bid: float = 0.0
    ask: float = 0.0


class PriceFeed:
    """
    Conecta a Binance WebSocket y mantiene historico de velas
    separado por (simbolo, timeframe).

    Acceso:
        feed.get_candles("BTC", "5m")  → List[Candle]
        feed.get_candles("BTC", "15m") → List[Candle]
        feed.get_price("BTC")          → float
    """

    SYMBOL_MAP = {
        "BTC": "btcusdt",
        "ETH": "ethusdt",
        "SOL": "solusdt",
        "BNB": "bnbusdt",
        "MATIC": "maticusdt",
        "AVAX": "avaxusdt",
        "LINK": "linkusdt",
        "ARB": "arbusdt",
    }

    def __init__(self, symbols: List[str]):
        self.symbols = symbols

        # candles[symbol][timeframe] → deque de Candle
        self.candles: Dict[str, Dict[str, deque]] = {
            sym: {tf: deque(maxlen=cfg.PRICE_HISTORY_LIMIT) for tf in TIMEFRAMES}
            for sym in symbols
        }

        self.tickers: Dict[str, TickerData] = {}
        self._callbacks: List[Callable] = []
        self._running = False

    # ------------------------------------------------------------------ #
    # API publica                                                          #
    # ------------------------------------------------------------------ #

    def add_callback(self, fn: Callable) -> None:
        """Registra callback llamado en cada tick de miniTicker."""
        self._callbacks.append(fn)

    def get_price(self, symbol: str) -> Optional[float]:
        ticker = self.tickers.get(symbol)
        return ticker.price if ticker else None

    def get_candles(self, symbol: str, timeframe: str) -> List[Candle]:
        """Retorna lista de velas (mas antigua primero) para symbol/TF."""
        return list(self.candles.get(symbol, {}).get(timeframe, []))

    def get_last_n_closes(self, symbol: str, timeframe: str, n: int) -> List[float]:
        """Retorna los ultimos N cierres para symbol/TF."""
        candles = self.get_candles(symbol, timeframe)
        return [c.close for c in candles[-n:]]

    def has_enough_candles(self, symbol: str, timeframe: str, minimum: int) -> bool:
        return len(self.candles.get(symbol, {}).get(timeframe, [])) >= minimum

    def candle_counts(self, symbol: str) -> Dict[str, int]:
        """Retorna {timeframe: num_candles} para un simbolo."""
        return {
            tf: len(deq)
            for tf, deq in self.candles.get(symbol, {}).items()
        }

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        self._running = True
        log.info(f"Iniciando feeds MTF ({'/'.join(TIMEFRAMES)}) para: {self.symbols}")
        tasks = [self._stream_symbol(sym) for sym in self.symbols]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------ #
    # WebSocket por simbolo                                                #
    # ------------------------------------------------------------------ #

    async def _stream_symbol(self, symbol: str) -> None:
        ws_sym = self.SYMBOL_MAP.get(symbol, f"{symbol.lower()}usdt")

        # Un unico stream combinado: 5m kline + 15m kline + mini ticker
        streams = "/".join([
            f"{ws_sym}@kline_{cfg.TF_ENTRY}",
            f"{ws_sym}@kline_{cfg.TF_TREND}",
            f"{ws_sym}@miniTicker",
        ])
        url = f"{cfg.BINANCE_WS_BASE}/{streams}"

        backoff = 2
        while self._running:
            try:
                async with websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=5,
                ) as ws:
                    log.info(f"[{symbol}] WS conectado → {cfg.TF_ENTRY}/{cfg.TF_TREND} klines + ticker")
                    backoff = 2
                    async for raw in ws:
                        if not self._running:
                            break
                        try:
                            msg = json.loads(raw)
                            # Multi-stream: {"stream": "...", "data": {...}}
                            data = msg.get("data", msg)
                            event = data.get("e", "")

                            if event == "kline":
                                self._process_kline(symbol, data)
                            elif event == "24hrMiniTicker":
                                self._process_ticker(symbol, data)
                        except Exception as e:
                            log.warning(f"[{symbol}] Error procesando msg: {e}")

            except Exception as e:
                if self._running:
                    log.error(
                        f"[{symbol}] WS error: {e}. "
                        f"Reconectando en {backoff}s"
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 60)

    # ------------------------------------------------------------------ #
    # Procesado de mensajes                                                #
    # ------------------------------------------------------------------ #

    def _process_kline(self, symbol: str, data: dict) -> None:
        k = data["k"]
        tf = k["i"]  # "5m" o "15m"

        if tf not in TIMEFRAMES:
            return  # ignorar otros TFs que pudieran llegar

        candle = Candle(
            timestamp=datetime.fromtimestamp(k["t"] / 1000),
            open=float(k["o"]),
            high=float(k["h"]),
            low=float(k["l"]),
            close=float(k["c"]),
            volume=float(k["v"]),
            is_closed=k["x"],
        )

        deq = self.candles[symbol][tf]

        if candle.is_closed:
            deq.append(candle)
            counts = self.candle_counts(symbol)
            log.debug(
                f"[{symbol}][{tf}] Vela cerrada {candle.close:,.4f} | "
                f"5m={counts['5m']} 15m={counts['15m']} velas"
            )
        else:
            # Vela activa: actualizar la ultima entrada si todavia esta abierta
            if deq and not deq[-1].is_closed:
                deq[-1] = candle
            else:
                deq.append(candle)

    def _process_ticker(self, symbol: str, data: dict) -> None:
        ticker = TickerData(
            symbol=symbol,
            price=float(data["c"]),
            timestamp=datetime.fromtimestamp(data["E"] / 1000),
        )
        self.tickers[symbol] = ticker

        loop = asyncio.get_event_loop()
        for cb in self._callbacks:
            loop.call_soon(
                lambda t=ticker, fn=cb: asyncio.ensure_future(self._safe_cb(fn, t))
            )

    async def _safe_cb(self, fn: Callable, ticker: TickerData) -> None:
        try:
            if asyncio.iscoroutinefunction(fn):
                await fn(ticker)
            else:
                fn(ticker)
        except Exception as e:
            log.warning(f"Error en ticker callback: {e}")
