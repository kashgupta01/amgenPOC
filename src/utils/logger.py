import logging
import os
import sys
from pathlib import Path

# APP_ENV controls which log file is written and the minimum log level.
# Set via environment variable; defaults to "dev" locally.
# Dockerfile sets APP_ENV=prod; pytest sets APP_ENV=test (or leaves it unset).
_ENV = os.getenv("APP_ENV", "dev").lower()

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

_LOG_FILE = LOG_DIR / f"{_ENV}.log"

_LEVEL_PER_ENV: dict[str, int] = {
    "prod": logging.INFO,    # production: skip DEBUG noise
    "test": logging.WARNING, # test runs: only warnings and errors
    "dev":  logging.DEBUG,   # local development: everything
}
_LOG_LEVEL = _LEVEL_PER_ENV.get(_ENV, logging.DEBUG)

_fmt = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# One file handler shared by all loggers so the file is opened (and cleared)
# exactly once per process start, not once per module that calls get_logger().
_file_handler = logging.FileHandler(_LOG_FILE, mode="w", encoding="utf-8")
_file_handler.setFormatter(_fmt)
_file_handler.setLevel(_LOG_LEVEL)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(_LOG_LEVEL)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(_fmt)
    stdout_handler.setLevel(_LOG_LEVEL)

    logger.addHandler(stdout_handler)
    logger.addHandler(_file_handler)
    logger.propagate = False
    return logger
