"""
Feed de precios en tiempo real via Binance WebSocket.
Acumula velas OHLCV y precios tick por tick para cada simbolo.
"""
import asyncio
import json
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional

import websockets

from config import cfg
from src.logger import setup_logger

log = setup_logger("price_feed")


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
    y precio actual por simbolo.
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
        self.candles: Dict[str, deque[Candle]] = {
            s: deque(maxlen=cfg.PRICE_HISTORY_LIMIT) for s in symbols
        }
        self.tickers: Dict[str, TickerData] = {}
        self._callbacks: List[Callable] = []
        self._running = False
        self._ws_tasks: List[asyncio.Task] = []

    def add_callback(self, fn: Callable) -> None:
        """Registra callback que se llama en cada tick."""
        self._callbacks.append(fn)

    def get_price(self, symbol: str) -> Optional[float]:
        ticker = self.tickers.get(symbol)
        return ticker.price if ticker else None

    def get_candles(self, symbol: str) -> List[Candle]:
        return list(self.candles.get(symbol, []))

    def get_last_n_closes(self, symbol: str, n: int) -> List[float]:
        candles = self.get_candles(symbol)
        return [c.close for c in candles[-n:]]

    async def start(self) -> None:
        self._running = True
        log.info(f"Iniciando feeds para: {self.symbols}")
        tasks = [self._stream_symbol(s) for s in self.symbols]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop(self) -> None:
        self._running = False
        for task in self._ws_tasks:
            task.cancel()

    async def _stream_symbol(self, symbol: str) -> None:
        ws_symbol = self.SYMBOL_MAP.get(symbol, f"{symbol.lower()}usdt")
        # Combinamos kline y mini ticker en un stream multi
        stream = f"{ws_symbol}@kline_{cfg.CANDLE_INTERVAL}/{ws_symbol}@miniTicker"
        url = f"{cfg.BINANCE_WS_BASE}/{stream}"

        backoff = 2
        while self._running:
            try:
                async with websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=5,
                ) as ws:
                    log.info(f"[{symbol}] WebSocket conectado: {url}")
                    backoff = 2
                    async for raw in ws:
                        if not self._running:
                            break
                        try:
                            msg = json.loads(raw)
                            # Multi-stream wraps in {"stream":..., "data":...}
                            data = msg.get("data", msg)
                            event = data.get("e", "")

                            if event == "kline":
                                self._process_kline(symbol, data)
                            elif event == "24hrMiniTicker":
                                self._process_ticker(symbol, data)
                        except Exception as e:
                            log.warning(f"[{symbol}] Error procesando mensaje: {e}")

            except Exception as e:
                if self._running:
                    log.error(f"[{symbol}] WebSocket error: {e}. Reconectando en {backoff}s")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 60)

    def _process_kline(self, symbol: str, data: dict) -> None:
        k = data["k"]
        candle = Candle(
            timestamp=datetime.fromtimestamp(k["t"] / 1000),
            open=float(k["o"]),
            high=float(k["h"]),
            low=float(k["l"]),
            close=float(k["c"]),
            volume=float(k["v"]),
            is_closed=k["x"],
        )

        candles = self.candles[symbol]
        if candle.is_closed:
            # Vela cerrada: agregar al historico
            candles.append(candle)
            log.debug(f"[{symbol}] Vela cerrada: {candle.close:.4f}")
        else:
            # Vela en curso: actualizar la ultima si ya existe
            if candles and not candles[-1].is_closed:
                candles[-1] = candle
            else:
                candles.append(candle)

    def _process_ticker(self, symbol: str, data: dict) -> None:
        ticker = TickerData(
            symbol=symbol,
            price=float(data["c"]),
            timestamp=datetime.fromtimestamp(data["E"] / 1000),
        )
        self.tickers[symbol] = ticker

        for cb in self._callbacks:
            try:
                asyncio.get_event_loop().call_soon(
                    lambda t=ticker: asyncio.ensure_future(self._safe_cb(cb, t))
                )
            except Exception:
                pass

    async def _safe_cb(self, fn: Callable, ticker: TickerData) -> None:
        try:
            if asyncio.iscoroutinefunction(fn):
                await fn(ticker)
            else:
                fn(ticker)
        except Exception as e:
            log.warning(f"Error en callback: {e}")
