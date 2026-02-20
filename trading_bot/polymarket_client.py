"""
Polymarket CLOB client wrapper.

Handles:
- Authentication via private key (EOA wallet)
- Fetching and filtering active BTC/Bitcoin price markets
- Retrieving current YES/NO prices from the order book
- Placing FOK (Fill-or-Kill) orders for arbitrage execution

Polymarket uses USDC on Polygon (chain_id=137).
Minimum order size is typically $1.
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Optional

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.constants import BUY, SELL  # noqa: F401 – re-exported

from trading_bot.config import cfg
from trading_bot.logger import logger

# Keywords that indicate a BTC/Bitcoin *price* market (not dominance, etc.)
_BTC_PRICE_KEYWORDS = re.compile(
    r"\b(bitcoin|btc)\b.{0,80}\$[\d,]+", re.I
)

# Minimum USDC liquidity on best ask/bid to bother with
MIN_LIQUIDITY_USDC = 5.0


@dataclass
class Token:
    token_id: str
    outcome: str     # "Yes" or "No"
    price: float     # current mid-price (0.0–1.0)


@dataclass
class Market:
    condition_id: str
    question: str
    tokens: list[Token]
    end_date_iso: Optional[str]
    active: bool
    closed: bool
    minimum_order_size: float = 1.0

    @property
    def yes_token(self) -> Optional[Token]:
        for t in self.tokens:
            if t.outcome.lower() == "yes":
                return t
        return None

    @property
    def no_token(self) -> Optional[Token]:
        for t in self.tokens:
            if t.outcome.lower() == "no":
                return t
        return None


@dataclass
class OrderResult:
    success: bool
    order_id: Optional[str] = None
    error: Optional[str] = None
    filled_usdc: float = 0.0
    avg_price: float = 0.0


class PolymarketClient:
    """Async-friendly wrapper around py-clob-client."""

    def __init__(self) -> None:
        self._client: Optional[ClobClient] = None
        self._loop = asyncio.get_event_loop()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _build_client(self) -> ClobClient:
        """Create and authenticate the CLOB client (blocking, run once)."""
        key = cfg.polymarket_private_key
        if not key.startswith("0x"):
            key = "0x" + key

        client = ClobClient(
            host=cfg.polymarket_host,
            chain_id=cfg.polymarket_chain_id,
            key=key,
            signature_type=0,  # EOA wallet
        )

        # Derive / create API credentials from the private key
        try:
            api_creds = client.create_or_derive_api_creds()
            client.set_api_creds(api_creds)
            logger.info(
                "Polymarket CLOB authenticated (api_key={}…)",
                api_creds.api_key[:8],
            )
        except Exception as exc:
            logger.error("Failed to derive Polymarket API creds: {}", exc)
            raise

        return client

    async def connect(self) -> None:
        """Authenticate and verify connectivity."""
        self._client = await asyncio.to_thread(self._build_client)
        logger.info("Polymarket client ready (host={})", cfg.polymarket_host)

    # ------------------------------------------------------------------
    # Market discovery
    # ------------------------------------------------------------------

    async def get_btc_markets(self) -> list[Market]:
        """
        Return all active, non-closed BTC price markets.
        Paginates through the CLOB market list automatically.
        """
        assert self._client is not None, "Call connect() first"

        markets: list[Market] = []
        cursor = ""

        while True:
            try:
                resp = await asyncio.to_thread(
                    self._client.get_markets, cursor
                )
            except Exception as exc:
                logger.error("Error fetching Polymarket markets: {}", exc)
                break

            data = resp.get("data", [])
            next_cursor = resp.get("next_cursor", "LTE=")

            for raw in data:
                market = _parse_market(raw)
                if market is None:
                    continue
                if market.closed or not market.active:
                    continue
                if not _BTC_PRICE_KEYWORDS.search(market.question):
                    continue
                markets.append(market)

            # CLOB uses base64-encoded cursors; "LTE=" means end of list
            if not next_cursor or next_cursor == "LTE=":
                break
            cursor = next_cursor

        logger.info("Found {} active BTC price markets on Polymarket", len(markets))
        return markets

    # ------------------------------------------------------------------
    # Live prices (order book mid)
    # ------------------------------------------------------------------

    async def refresh_market_prices(self, market: Market) -> Market:
        """
        Fetch the current best bid/ask from the CLOB and update token prices.
        Returns the same market object (mutated in place).
        """
        assert self._client is not None

        for token in market.tokens:
            try:
                book = await asyncio.to_thread(
                    self._client.get_order_book, token.token_id
                )
                bids = book.bids or []
                asks = book.asks or []

                best_bid = float(bids[0].price) if bids else 0.0
                best_ask = float(asks[0].price) if asks else 1.0
                mid = (best_bid + best_ask) / 2.0
                token.price = round(mid, 4)
            except Exception as exc:
                logger.debug(
                    "Could not refresh price for token {}: {}", token.token_id[:10], exc
                )

        return market

    # ------------------------------------------------------------------
    # Order execution
    # ------------------------------------------------------------------

    async def place_order(
        self,
        token_id: str,
        side: str,           # BUY or SELL (use constants from this module)
        price: float,        # limit price (0.0–1.0)
        size_usdc: float,    # dollar amount to spend
        order_type: str = OrderType.FOK,
    ) -> OrderResult:
        """
        Place a limit order on the CLOB.

        size_usdc: how many USDC to spend (client converts to token qty).
        price:     limit price in probability space (e.g. 0.45 for 45 ¢).
        """
        assert self._client is not None

        # Round price to nearest tick (Polymarket uses 0.01 ticks)
        price = round(price, 2)
        size_usdc = round(size_usdc, 2)

        if size_usdc < 1.0:
            return OrderResult(success=False, error="Size below $1 minimum")

        order_args = OrderArgs(
            token_id=token_id,
            price=price,
            size=size_usdc,
            side=side,
        )

        try:
            signed_order = await asyncio.to_thread(
                self._client.create_order, order_args
            )
            resp = await asyncio.to_thread(
                self._client.post_order, signed_order, order_type
            )

            order_id = resp.get("orderID", "") or resp.get("id", "")
            status = resp.get("status", "")
            error_msg = resp.get("errorMsg", "") or resp.get("error", "")

            if error_msg:
                logger.warning("Order rejected: {}", error_msg)
                return OrderResult(success=False, error=error_msg)

            logger.info(
                "Order placed: id={} status={} price={} size_usdc={}",
                order_id[:12] if order_id else "?",
                status,
                price,
                size_usdc,
            )
            return OrderResult(
                success=True,
                order_id=order_id,
                filled_usdc=size_usdc,
                avg_price=price,
            )

        except Exception as exc:
            logger.error("Order placement failed: {}", exc)
            return OrderResult(success=False, error=str(exc))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_market(raw: dict) -> Optional[Market]:
    try:
        tokens = [
            Token(
                token_id=t["token_id"],
                outcome=t.get("outcome", ""),
                price=float(t.get("price", 0.5)),
            )
            for t in raw.get("tokens", [])
        ]
        return Market(
            condition_id=raw["condition_id"],
            question=raw.get("question", ""),
            tokens=tokens,
            end_date_iso=raw.get("end_date_iso") or raw.get("end_date"),
            active=bool(raw.get("active", False)),
            closed=bool(raw.get("closed", False)),
            minimum_order_size=float(raw.get("minimum_order_size", 1.0)),
        )
    except (KeyError, ValueError, TypeError) as exc:
        logger.debug("Skipping unparseable market: {}", exc)
        return None
