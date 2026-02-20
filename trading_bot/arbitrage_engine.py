"""
Core arbitrage engine.

For every active BTC price market on Polymarket:
  1. Parse the market question to extract strike price and expiry.
  2. Compute the theoretical YES probability using the lognormal model
     and the live Binance BTC spot price.
  3. Compare with the current Polymarket market price (implied probability).
  4. If |theoretical - market| > MIN_EDGE_THRESHOLD → attempt a trade.

Trade direction:
  • theoretical > market  →  BUY YES  (market underestimates probability)
  • theoretical < market  →  BUY NO   (market overestimates YES probability)

Execution:
  • FOK (Fill-or-Kill) limit order at a price that captures ≥50% of the edge.
  • Risk manager approves size before any order is sent.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from py_clob_client.constants import BUY

from trading_bot.config import cfg
from trading_bot.logger import logger
from trading_bot.polymarket_client import Market, PolymarketClient, Token
from trading_bot.pricing_model import MarketParams, parse_market_question, theoretical_probability
from trading_bot.risk_manager import RiskManager, Side


@dataclass
class Opportunity:
    market: Market
    params: MarketParams
    yes_token: Token
    no_token: Token
    spot: float
    theoretical_prob: float
    market_yes_price: float
    edge: float          # theoretical - market_yes_price (signed)
    side: Side           # which token to buy
    limit_price: float   # order price


class ArbitrageEngine:
    """
    Scans Polymarket BTC markets and fires trades when edge exceeds threshold.
    """

    def __init__(
        self,
        poly_client: PolymarketClient,
        risk_manager: RiskManager,
        annual_vol: float,
        bankroll_usdc: float = 0.0,
    ) -> None:
        self._poly = poly_client
        self._risk = risk_manager
        self._vol = annual_vol
        self._bankroll = bankroll_usdc

        self._markets: list[Market] = []
        self._last_scan: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_vol(self, annual_vol: float) -> None:
        self._vol = annual_vol

    def update_bankroll(self, usdc: float) -> None:
        self._bankroll = usdc

    async def refresh_markets(self) -> None:
        """Reload active BTC markets from Polymarket (call every N minutes)."""
        try:
            self._markets = await self._poly.get_btc_markets()
            self._last_scan = datetime.now(timezone.utc)
            logger.info(
                "Market refresh complete: {} BTC markets tracked", len(self._markets)
            )
        except Exception as exc:
            logger.error("Market refresh failed: {}", exc)

    async def evaluate(self, spot: float) -> list[Opportunity]:
        """
        Evaluate all tracked markets at current BTC spot price.
        Returns list of actionable opportunities (may be empty).

        Opportunities are also executed automatically if risk manager approves.
        """
        if not self._markets:
            logger.debug("No markets loaded yet – skipping evaluation")
            return []

        opportunities: list[Opportunity] = []
        now = datetime.now(timezone.utc)

        for market in self._markets:
            opp = await self._evaluate_single(market, spot, now)
            if opp is not None:
                opportunities.append(opp)
                await self._execute(opp)

        return opportunities

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _evaluate_single(
        self, market: Market, spot: float, now: datetime
    ) -> Optional[Opportunity]:
        """
        Returns an Opportunity if this market has tradeable edge, else None.
        """
        yes_token = market.yes_token
        no_token = market.no_token
        if yes_token is None or no_token is None:
            return None

        # Parse the question (only if not already cached)
        params = parse_market_question(market.question, market.end_date_iso)
        if params is None:
            return None

        # Compute theoretical probability
        prob = theoretical_probability(spot, params, self._vol, now=now)
        if prob != prob:  # NaN → expired market
            return None

        # Guard extreme probabilities (near certainty – no edge to capture)
        if not (cfg.min_market_prob < prob < cfg.max_market_prob):
            return None

        # Refresh live prices from CLOB
        market = await self._poly.refresh_market_prices(market)
        yes_token = market.yes_token
        if yes_token is None:
            return None

        market_price = yes_token.price
        edge = prob - market_price

        logger.debug(
            "  Q: {} | strike={} | spot={:.0f} | model={:.3f} | mkt={:.3f} | edge={:+.3f}",
            market.question[:70],
            params.strike,
            spot,
            prob,
            market_price,
            edge,
        )

        if abs(edge) < cfg.min_edge_threshold:
            return None

        # Determine trade side and limit price
        # We pay slightly more than mid to improve fill probability,
        # but still capture at least half the edge.
        if edge > 0:
            # Buy YES: market undervalues the event
            side: Side = "YES"
            # Place limit slightly above current ask (mid + half edge)
            limit_price = min(market_price + abs(edge) * 0.5, 0.99)
            token = yes_token
        else:
            # Buy NO: market overvalues the event
            side = "NO"
            no_price = 1.0 - market_price
            limit_price = min(no_price + abs(edge) * 0.5, 0.99)
            token = no_token

        return Opportunity(
            market=market,
            params=params,
            yes_token=yes_token,
            no_token=no_token if no_token else yes_token,
            spot=spot,
            theoretical_prob=prob,
            market_yes_price=market_price,
            edge=edge,
            side=side,
            limit_price=round(limit_price, 2),
        )

    async def _execute(self, opp: Opportunity) -> None:
        """Size and submit the order for a detected opportunity."""
        decision = self._risk.size_position(
            condition_id=opp.market.condition_id,
            side=opp.side,
            market_price=opp.market_yes_price,
            theoretical_prob=opp.theoretical_prob,
            bankroll_usdc=self._bankroll,
        )

        if not decision.approved:
            logger.info(
                "Trade SKIPPED [{}] | reason: {}",
                opp.market.question[:60],
                decision.reason,
            )
            return

        logger.info(
            "Trade SIGNAL: {} {} | edge={:+.3f} | price={:.3f} | size=${:.2f} | {}",
            opp.side,
            opp.market.question[:60],
            opp.edge,
            opp.limit_price,
            decision.size_usdc,
            decision.reason,
        )

        token = opp.yes_token if opp.side == "YES" else opp.no_token

        result = await self._poly.place_order(
            token_id=token.token_id,
            side=BUY,
            price=opp.limit_price,
            size_usdc=decision.size_usdc,
        )

        if result.success:
            self._risk.open_position(
                condition_id=opp.market.condition_id,
                question=opp.market.question,
                side=opp.side,
                size_usdc=decision.size_usdc,
                entry_price=opp.limit_price,
                theoretical_prob=opp.theoretical_prob,
            )
            # Reduce available bankroll optimistically
            self._bankroll = max(0.0, self._bankroll - decision.size_usdc)
            logger.info(
                "Order FILLED: {} | order_id={} | remaining_bankroll=${:.2f}",
                opp.market.question[:60],
                result.order_id or "?",
                self._bankroll,
            )
        else:
            logger.warning(
                "Order FAILED: {} | error={}",
                opp.market.question[:60],
                result.error,
            )
