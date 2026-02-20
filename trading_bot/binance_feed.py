"""
Real-time BTC/USDT price feed via Binance WebSocket.

Subscribes to the 24h ticker stream so we get the latest trade price
with minimal latency. Falls back and reconnects automatically on any error.
"""
import asyncio
import json
from typing import Callable, Awaitable, Optional
import websockets
from websockets.exceptions import ConnectionClosed
import httpx

from trading_bot.config import cfg
from trading_bot.logger import logger

PriceCallback = Callable[[float], Awaitable[None]]


class BinanceFeed:
    """Maintains a live BTC/USDT price and notifies registered callbacks."""

    def __init__(self) -> None:
        self._price: Optional[float] = None
        self._callbacks: list[PriceCallback] = []
        self._running = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def price(self) -> Optional[float]:
        """Latest BTC/USDT price (None until first tick received)."""
        return self._price

    def register_callback(self, cb: PriceCallback) -> None:
        """Register an async callback that fires on every price update."""
        self._callbacks.append(cb)

    async def run(self) -> None:
        """Start the feed. Runs forever until cancelled."""
        self._running = True
        stream = "btcusdt@aggTrade"
        url = f"{cfg.binance_ws_url}/{stream}"

        logger.info("Connecting to Binance WebSocket: {}", url)

        backoff = 1.0
        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    backoff = 1.0
                    logger.info("Binance WebSocket connected")
                    async for raw in ws:
                        msg = json.loads(raw)
                        # aggTrade message: price is in field "p"
                        price = float(msg["p"])
                        await self._on_price(price)
            except ConnectionClosed as exc:
                logger.warning("Binance WebSocket closed: {}. Reconnecting in {}s…", exc, backoff)
            except Exception as exc:
                logger.error("Binance WebSocket error: {}. Reconnecting in {}s…", exc, backoff)

            if not self._running:
                break
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)

    def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # Historical volatility
    # ------------------------------------------------------------------

    async def fetch_realized_volatility(
        self, lookback_days: int = 30, interval: str = "1d"
    ) -> float:
        """
        Fetch daily close prices from Binance REST and compute
        annualised realized volatility (std of log returns).

        Falls back to 80% if the request fails.
        """
        if cfg.btc_annual_vol_override > 0:
            logger.info(
                "Using BTC vol override from config: {:.1%}", cfg.btc_annual_vol_override
            )
            return cfg.btc_annual_vol_override

        url = f"{cfg.binance_rest_url}/api/v3/klines"
        params = {
            "symbol": "BTCUSDT",
            "interval": interval,
            "limit": lookback_days + 1,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                klines = resp.json()

            import numpy as np

            closes = [float(k[4]) for k in klines]
            log_returns = np.diff(np.log(closes))
            daily_vol = float(np.std(log_returns, ddof=1))
            annual_vol = daily_vol * (365 ** 0.5)

            logger.info(
                "BTC realized vol ({}d): {:.1%}", lookback_days, annual_vol
            )
            return annual_vol
        except Exception as exc:
            logger.warning("Could not fetch BTC volatility: {}. Using 80% fallback.", exc)
            return 0.80

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _on_price(self, price: float) -> None:
        changed = self._price != price
        self._price = price
        if changed and self._callbacks:
            await asyncio.gather(*[cb(price) for cb in self._callbacks])
