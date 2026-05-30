import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

_fmt = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _build_handler(stream) -> logging.StreamHandler:
    h = logging.StreamHandler(stream)
    h.setFormatter(_fmt)
    return h


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.addHandler(_build_handler(sys.stdout))

    #what does this line do? It adds a file handler to the logger that writes log messages to a file named "app.log" in the LOG_DIR directory. The log messages are formatted using the _fmt formatter, and the file handler is set to capture all log messages at the DEBUG level and above.
    #will this line create app.log? Yes, if the file does not already exist, it will be created when the logger writes to it for the first time.
    file_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    file_handler.setFormatter(_fmt)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
