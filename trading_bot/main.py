"""
AION Trading Bot – entry point.

Runs three concurrent async tasks:
  1. Binance WebSocket price feed (continuous)
  2. Polymarket market scanner (every MARKET_SCAN_INTERVAL seconds)
  3. Arbitrage evaluation loop (every ARBITRAGE_CHECK_INTERVAL seconds,
     also triggered by significant price moves)

Usage:
    python -m trading_bot.main

Or, after 'pip install -e .':
    aion-bot
"""
from __future__ import annotations

import asyncio
import signal
import sys
from datetime import datetime, timezone
from typing import Optional

from trading_bot.config import cfg
from trading_bot.logger import logger, setup_logger
from trading_bot.binance_feed import BinanceFeed
from trading_bot.polymarket_client import PolymarketClient
from trading_bot.risk_manager import RiskManager
from trading_bot.arbitrage_engine import ArbitrageEngine

# Minimum BTC price change (absolute, USD) to trigger an immediate evaluation
PRICE_TRIGGER_DELTA = 100.0


async def fetch_polymarket_balance(poly: PolymarketClient) -> float:
    """
    Attempt to fetch the USDC balance from Polymarket.
    Returns 0 on failure (bot will skip trades until manually updated).
    """
    try:
        balance_resp = await asyncio.to_thread(poly._client.get_balance_allowance)
        # Response structure varies by py-clob-client version; handle both
        usdc = float(
            balance_resp.get("balance", 0)
            or balance_resp.get("USDC", {}).get("balance", 0)
            or 0
        )
        logger.info("Polymarket USDC balance: ${:.2f}", usdc)
        return usdc
    except Exception as exc:
        logger.warning("Could not fetch Polymarket balance: {}. Defaulting to $0.", exc)
        return 0.0


class Bot:
    def __init__(self) -> None:
        self.feed = BinanceFeed()
        self.poly = PolymarketClient()
        self.risk = RiskManager()
        self.engine: Optional[ArbitrageEngine] = None
        self._shutdown = asyncio.Event()
        self._last_evaluated_price: Optional[float] = None

    async def _on_price_update(self, price: float) -> None:
        """Called by BinanceFeed on every new trade price."""
        if self.engine is None:
            return

        # Trigger evaluation on significant price move OR periodic schedule
        last = self._last_evaluated_price
        if last is None or abs(price - last) >= PRICE_TRIGGER_DELTA:
            self._last_evaluated_price = price
            try:
                await self.engine.evaluate(price)
            except Exception as exc:
                logger.error("Evaluation error at spot={:.2f}: {}", price, exc)

    async def _market_scanner_loop(self) -> None:
        """Periodically refresh the list of active Polymarket markets."""
        while not self._shutdown.is_set():
            if self.engine is not None:
                await self.engine.refresh_markets()
                # Log risk status after each scan
                status = self.risk.status()
                logger.info(
                    "Risk snapshot: open={} exposure=${:.2f} realised_pnl=${:+.2f}",
                    status["open_positions"],
                    status["open_exposure_usdc"],
                    status["realised_pnl_usdc"],
                )
            try:
                await asyncio.wait_for(
                    self._shutdown.wait(),
                    timeout=cfg.market_scan_interval,
                )
            except asyncio.TimeoutError:
                pass  # expected – sleep elapsed

    async def _periodic_eval_loop(self) -> None:
        """
        Fallback evaluation loop – ensures we check even if price doesn't move.
        Useful for markets close to expiry where time decay matters.
        """
        while not self._shutdown.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown.wait(),
                    timeout=cfg.arbitrage_check_interval,
                )
            except asyncio.TimeoutError:
                pass

            if self.engine is not None and self.feed.price is not None:
                try:
                    await self.engine.evaluate(self.feed.price)
                except Exception as exc:
                    logger.error("Periodic evaluation error: {}", exc)

    async def run(self) -> None:
        setup_logger()
        logger.info("=" * 60)
        logger.info("AION Arbitrage Bot starting up")
        logger.info("  Polymarket host : {}", cfg.polymarket_host)
        logger.info("  Chain ID        : {}", cfg.polymarket_chain_id)
        logger.info("  Max position    : ${}", cfg.max_position_usdc)
        logger.info("  Min edge        : {:.1%}", cfg.min_edge_threshold)
        logger.info("  Kelly fraction  : {}", cfg.kelly_fraction)
        logger.info("=" * 60)

        # Validate configuration
        try:
            cfg.validate()
        except ValueError as exc:
            logger.error("Configuration error: {}", exc)
            sys.exit(1)

        # Connect to Polymarket
        logger.info("Connecting to Polymarket CLOB…")
        await self.poly.connect()

        # Fetch balance
        bankroll = await fetch_polymarket_balance(self.poly)

        # Fetch BTC volatility (blocking REST call, run once at startup)
        logger.info("Fetching BTC realized volatility…")
        annual_vol = await self.feed.fetch_realized_volatility(lookback_days=30)

        # Build the engine
        self.engine = ArbitrageEngine(
            poly_client=self.poly,
            risk_manager=self.risk,
            annual_vol=annual_vol,
            bankroll_usdc=bankroll,
        )

        # Initial market load
        await self.engine.refresh_markets()

        # Register price callback
        self.feed.register_callback(self._on_price_update)

        # Launch all tasks
        logger.info("All systems ready. Starting live trading loop…")
        tasks = [
            asyncio.create_task(self.feed.run(), name="binance-feed"),
            asyncio.create_task(self._market_scanner_loop(), name="market-scanner"),
            asyncio.create_task(self._periodic_eval_loop(), name="periodic-eval"),
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Bot shut down cleanly.")
        finally:
            for t in tasks:
                t.cancel()
            self.feed.stop()
            status = self.risk.status()
            logger.info("Final risk snapshot: {}", status)
            logger.info("AION Bot stopped.")

    def request_shutdown(self) -> None:
        logger.info("Shutdown requested…")
        self._shutdown.set()
        self.feed.stop()


async def _async_main() -> None:
    bot = Bot()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, bot.request_shutdown)

    await bot.run()


def main() -> None:
    try:
        asyncio.run(_async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
