"""
Logging setup using loguru.
"""
import sys
import os
from loguru import logger as _logger
from trading_bot.config import cfg


def setup_logger() -> None:
    _logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
        "{message}"
    )

    # Console output
    _logger.add(
        sys.stdout,
        format=log_format,
        level=cfg.log_level,
        colorize=True,
    )

    # File output
    log_dir = os.path.dirname(cfg.log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    _logger.add(
        cfg.log_file,
        format=log_format,
        level=cfg.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        colorize=False,
    )

    _logger.info("Logger initialized (level={})", cfg.log_level)


# Re-export for convenience
logger = _logger
