"""
Logger con colores para el bot.
"""
import logging
import os
import sys
import colorlog
from config import cfg


def setup_logger(name: str) -> logging.Logger:
    os.makedirs(os.path.dirname(cfg.LOG_FILE), exist_ok=True)

    handler = colorlog.StreamHandler(sys.stdout)
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(name)s] %(levelname)s%(reset)s  %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )

    file_handler = logging.FileHandler(cfg.LOG_FILE)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(name)s] %(levelname)s  %(message)s")
    )

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, cfg.LOG_LEVEL.upper(), logging.INFO))
    logger.addHandler(handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
