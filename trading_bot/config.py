"""
Configuration loader – reads from .env file and environment variables.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _get_float(key: str, default: float = 0.0) -> float:
    raw = _get(key)
    return float(raw) if raw else default


def _get_int(key: str, default: int = 0) -> int:
    raw = _get(key)
    return int(raw) if raw else default


@dataclass
class Config:
    # Polymarket
    polymarket_private_key: str = field(
        default_factory=lambda: _get("POLYMARKET_PRIVATE_KEY")
    )
    polymarket_host: str = field(
        default_factory=lambda: _get("POLYMARKET_HOST", "https://clob.polymarket.com")
    )
    polymarket_chain_id: int = field(
        default_factory=lambda: _get_int("POLYMARKET_CHAIN_ID", 137)
    )

    # Binance
    binance_ws_url: str = field(
        default_factory=lambda: _get("BINANCE_WS_URL", "wss://stream.binance.com:9443/ws")
    )
    binance_rest_url: str = field(
        default_factory=lambda: _get("BINANCE_REST_URL", "https://api.binance.com")
    )

    # Risk management
    max_position_usdc: float = field(
        default_factory=lambda: _get_float("MAX_POSITION_USDC", 200.0)
    )
    min_edge_threshold: float = field(
        default_factory=lambda: _get_float("MIN_EDGE_THRESHOLD", 0.015)
    )
    max_total_exposure_usdc: float = field(
        default_factory=lambda: _get_float("MAX_TOTAL_EXPOSURE_USDC", 1000.0)
    )
    kelly_fraction: float = field(
        default_factory=lambda: _get_float("KELLY_FRACTION", 0.5)
    )
    min_market_prob: float = field(
        default_factory=lambda: _get_float("MIN_MARKET_PROB", 0.02)
    )
    max_market_prob: float = field(
        default_factory=lambda: _get_float("MAX_MARKET_PROB", 0.98)
    )

    # Bot behaviour
    market_scan_interval: int = field(
        default_factory=lambda: _get_int("MARKET_SCAN_INTERVAL_SECONDS", 300)
    )
    arbitrage_check_interval: int = field(
        default_factory=lambda: _get_int("ARBITRAGE_CHECK_INTERVAL_SECONDS", 10)
    )
    btc_annual_vol_override: float = field(
        default_factory=lambda: _get_float("BTC_ANNUAL_VOL_OVERRIDE", 0.0)
    )

    # Logging
    log_level: str = field(
        default_factory=lambda: _get("LOG_LEVEL", "INFO")
    )
    log_file: str = field(
        default_factory=lambda: _get("LOG_FILE", "logs/bot.log")
    )

    def validate(self) -> None:
        if not self.polymarket_private_key:
            raise ValueError(
                "POLYMARKET_PRIVATE_KEY is not set. "
                "Copy .env.example to .env and fill in your private key."
            )
        if self.max_position_usdc <= 0:
            raise ValueError("MAX_POSITION_USDC must be > 0")
        if not 0 < self.min_edge_threshold < 1:
            raise ValueError("MIN_EDGE_THRESHOLD must be between 0 and 1")


# Singleton
cfg = Config()
