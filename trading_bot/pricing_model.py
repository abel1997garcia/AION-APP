"""
Theoretical probability model for binary crypto price markets.

Strategy: Polymarket BTC markets ask "Will BTC be above $K at time T?"
We price that probability using a lognormal (GBM) model driven by the
live Binance price and realized volatility.

Formula (Black-Scholes risk-neutral probability):
    P(S_T > K) = N(d2)
    d2 = [ln(S/K) + (drift - σ²/2) · T] / (σ · √T)

Where:
    S     = current BTC spot price
    K     = strike (threshold in market question)
    T     = time to expiry in years
    σ     = annualised BTC volatility
    drift = 0 (risk-neutral; conservative choice)
    N(·)  = standard normal CDF
"""
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from scipy.stats import norm
from dateutil import parser as dateutil_parser

from trading_bot.logger import logger


@dataclass
class MarketParams:
    """Parsed parameters extracted from a Polymarket market question."""
    strike: float           # USD price threshold
    direction: str          # "above" or "below"
    expiry: datetime        # UTC expiry timestamp
    raw_question: str       # original question text


# ---------------------------------------------------------------------------
# Probability calculation
# ---------------------------------------------------------------------------

def probability_above(
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    annual_vol: float,
    drift: float = 0.0,
) -> float:
    """
    Return the risk-neutral probability that BTC closes above `strike`
    at expiry, given current spot price and annualised volatility.

    Returns 1.0 or 0.0 at expiry.
    """
    if time_to_expiry_years <= 0:
        return 1.0 if spot > strike else 0.0
    if annual_vol <= 0:
        return 1.0 if spot > strike else 0.0

    d2 = (
        np.log(spot / strike)
        + (drift - 0.5 * annual_vol ** 2) * time_to_expiry_years
    ) / (annual_vol * np.sqrt(time_to_expiry_years))

    return float(norm.cdf(d2))


def theoretical_probability(
    spot: float,
    params: MarketParams,
    annual_vol: float,
    now: Optional[datetime] = None,
) -> float:
    """
    Compute the model probability that a YES outcome resolves to True.

    For "above $K" markets  → P(S_T > K)
    For "below $K" markets  → 1 - P(S_T > K)
    """
    now = now or datetime.now(timezone.utc)
    dt = (params.expiry - now).total_seconds()
    if dt < 0:
        logger.debug("Market already expired: {}", params.raw_question)
        return float("nan")

    years = dt / (365.25 * 24 * 3600)
    p_above = probability_above(spot, params.strike, years, annual_vol)

    if params.direction == "above":
        return p_above
    else:  # "below"
        return 1.0 - p_above


# ---------------------------------------------------------------------------
# Market question parser
# ---------------------------------------------------------------------------

# Price patterns: $100,000 | $95k | $95K | $95.5k | $90,000.50
_PRICE_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*([kKmM]?)"
)

# "above" / "over" / ">" synonyms
_ABOVE_RE = re.compile(r"\b(above|over|exceed|higher|>|atleast|at least)\b", re.I)
_BELOW_RE = re.compile(r"\b(below|under|less than|lower|<)\b", re.I)

# Date patterns Polymarket uses: "January 31", "Jan 31, 2025", "31st Jan", ISO
_DATE_PATTERNS = [
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?",
    r"\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|"
    r"Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)(?:,?\s*\d{4})?",
    r"\d{4}-\d{2}-\d{2}",
]
_DATE_RE = re.compile("|".join(_DATE_PATTERNS), re.I)

# Relative time expressions
_EOW_RE = re.compile(r"\bend\s+of\s+(the\s+)?(week|month)\b", re.I)
_EOY_RE = re.compile(r"\bend\s+of\s+(the\s+)?(year|2\d{3})\b", re.I)


def _parse_price(text: str) -> Optional[float]:
    m = _PRICE_RE.search(text)
    if not m:
        return None
    digits = m.group(1).replace(",", "")
    multiplier_char = m.group(2).lower()
    value = float(digits)
    if multiplier_char == "k":
        value *= 1_000
    elif multiplier_char == "m":
        value *= 1_000_000
    return value


def _parse_expiry(text: str) -> Optional[datetime]:
    """Try several strategies to extract expiry date from question text."""
    # 1. Try dateutil directly on the whole question
    for m in _DATE_RE.finditer(text):
        raw_date = m.group(0)
        try:
            dt = dateutil_parser.parse(raw_date, dayfirst=False)
            # If no year was parsed, dateutil defaults to current year;
            # if resulting date is in the past, bump to next year.
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if dt < now:
                dt = dt.replace(year=dt.year + 1)
            # Set to end of day (23:59:59 UTC)
            return dt.replace(hour=23, minute=59, second=59)
        except (ValueError, OverflowError):
            continue

    # 2. Relative expressions
    now = datetime.now(timezone.utc)
    if _EOW_RE.search(text):
        days_ahead = 6 - now.weekday()  # days until Sunday
        target = now + __import__("datetime").timedelta(days=days_ahead)
        return target.replace(hour=23, minute=59, second=59)

    if _EOY_RE.search(text):
        return datetime(now.year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    return None


def parse_market_question(
    question: str, end_date_iso: Optional[str] = None
) -> Optional[MarketParams]:
    """
    Parse a Polymarket BTC binary market question.

    Returns MarketParams or None if the question cannot be parsed.
    """
    strike = _parse_price(question)
    if strike is None:
        return None

    if _ABOVE_RE.search(question):
        direction = "above"
    elif _BELOW_RE.search(question):
        direction = "below"
    else:
        # Default assumption for "BTC > $X" style (no keyword)
        direction = "above"

    # Prefer end_date_iso from market metadata
    expiry: Optional[datetime] = None
    if end_date_iso:
        try:
            expiry = dateutil_parser.isoparse(end_date_iso)
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass

    if expiry is None:
        expiry = _parse_expiry(question)

    if expiry is None:
        logger.debug("Could not parse expiry from: '{}'", question)
        return None

    return MarketParams(
        strike=strike,
        direction=direction,
        expiry=expiry,
        raw_question=question,
    )
