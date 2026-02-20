"""
Risk management module.

Responsibilities:
- Enforce per-position size limits
- Enforce total exposure limits
- Calculate optimal position size using fractional Kelly criterion
- Track open positions and realised P&L (in-memory for this session)

Kelly position sizing:
  Buy YES at market price p_m with theoretical probability p_t:
    f = (p_t - p_m) / (1 - p_m)   [fraction of bankroll]

  Buy NO at market price (1 - p_m) with theoretical prob (1 - p_t):
    f = (p_m - p_t) / p_m          [fraction of bankroll]

We apply cfg.kelly_fraction (default 0.5 = half-Kelly) and cap at
MAX_POSITION_USDC.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from trading_bot.config import cfg
from trading_bot.logger import logger


Side = Literal["YES", "NO"]


@dataclass
class Position:
    condition_id: str
    question: str
    side: Side
    size_usdc: float
    entry_price: float        # probability paid
    theoretical_prob: float   # model probability at entry
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SizeDecision:
    approved: bool
    size_usdc: float
    reason: str


class RiskManager:
    """Stateful risk manager; lives for the lifetime of the bot process."""

    def __init__(self) -> None:
        self._positions: dict[str, Position] = {}   # condition_id → Position
        self._realised_pnl: float = 0.0
        self._total_traded: float = 0.0

    # ------------------------------------------------------------------
    # Position sizing
    # ------------------------------------------------------------------

    def size_position(
        self,
        condition_id: str,
        side: Side,
        market_price: float,      # Polymarket implied probability of YES
        theoretical_prob: float,  # our model probability of YES
        bankroll_usdc: float,     # available USDC balance
    ) -> SizeDecision:
        """
        Return the approved trade size in USDC (or 0 if rejected).
        """
        # 1. Check if we already have a position in this market
        if condition_id in self._positions:
            return SizeDecision(
                approved=False,
                size_usdc=0.0,
                reason="Already have an open position in this market",
            )

        # 2. Check total exposure
        current_exposure = self._total_open_exposure()
        headroom = cfg.max_total_exposure_usdc - current_exposure
        if headroom <= 0:
            return SizeDecision(
                approved=False,
                size_usdc=0.0,
                reason=f"Max total exposure reached (${cfg.max_total_exposure_usdc:.0f})",
            )

        # 3. Kelly fraction
        kelly_f = self._kelly_fraction(side, market_price, theoretical_prob)
        if kelly_f <= 0:
            return SizeDecision(
                approved=False,
                size_usdc=0.0,
                reason=f"Kelly fraction non-positive ({kelly_f:.4f})",
            )

        raw_size = bankroll_usdc * cfg.kelly_fraction * kelly_f

        # 4. Apply hard caps
        size = min(raw_size, cfg.max_position_usdc, headroom, bankroll_usdc)
        size = round(size, 2)

        if size < 1.0:
            return SizeDecision(
                approved=False,
                size_usdc=0.0,
                reason=f"Computed size ${size:.2f} below $1 minimum",
            )

        return SizeDecision(
            approved=True,
            size_usdc=size,
            reason=(
                f"Kelly={kelly_f:.4f} | fraction={cfg.kelly_fraction} | "
                f"raw=${raw_size:.2f} | capped=${size:.2f}"
            ),
        )

    # ------------------------------------------------------------------
    # Position lifecycle
    # ------------------------------------------------------------------

    def open_position(
        self,
        condition_id: str,
        question: str,
        side: Side,
        size_usdc: float,
        entry_price: float,
        theoretical_prob: float,
    ) -> None:
        self._positions[condition_id] = Position(
            condition_id=condition_id,
            question=question,
            side=side,
            size_usdc=size_usdc,
            entry_price=entry_price,
            theoretical_prob=theoretical_prob,
        )
        self._total_traded += size_usdc
        logger.info(
            "Position opened: {} {} ${:.2f} @ {:.3f} (model={:.3f})",
            side, question[:60], size_usdc, entry_price, theoretical_prob,
        )

    def close_position(self, condition_id: str, outcome: bool) -> float:
        """
        Record a resolved position.
        outcome: True if YES won, False if NO won.
        Returns realised P&L for this position.
        """
        pos = self._positions.pop(condition_id, None)
        if pos is None:
            return 0.0

        won = (pos.side == "YES" and outcome) or (pos.side == "NO" and not outcome)
        if won:
            # Payout: size_usdc / entry_price  (shares * 1 USDC each)
            payout = pos.size_usdc / pos.entry_price
            pnl = payout - pos.size_usdc
        else:
            pnl = -pos.size_usdc

        self._realised_pnl += pnl
        logger.info(
            "Position closed: {} {} P&L={:+.2f} | cumulative={:+.2f}",
            pos.side, pos.question[:60], pnl, self._realised_pnl,
        )
        return pnl

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def status(self) -> dict:
        return {
            "open_positions": len(self._positions),
            "open_exposure_usdc": self._total_open_exposure(),
            "total_traded_usdc": self._total_traded,
            "realised_pnl_usdc": self._realised_pnl,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _total_open_exposure(self) -> float:
        return sum(p.size_usdc for p in self._positions.values())

    @staticmethod
    def _kelly_fraction(side: Side, market_price: float, theoretical_prob: float) -> float:
        """
        Compute the raw Kelly fraction (before applying cfg.kelly_fraction).

        Buy YES at market_price p_m, theoretical prob p_t:
            f = (p_t - p_m) / (1 - p_m)

        Buy NO at price (1 - p_m), theoretical NO prob (1 - p_t):
            f = (p_m - p_t) / p_m
        """
        eps = 1e-6  # guard against division by zero

        if side == "YES":
            denom = max(1.0 - market_price, eps)
            return (theoretical_prob - market_price) / denom
        else:  # NO
            denom = max(market_price, eps)
            return (market_price - theoretical_prob) / denom
