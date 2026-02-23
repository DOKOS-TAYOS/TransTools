"""Logging configuration for TransTools."""

import logging
import sys
from pathlib import Path
from typing import Optional

# Will be set after config is loaded
_logger: Optional[logging.Logger] = None


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_console: bool = False,
) -> None:
    """Configure application logging.

    Args:
        log_level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_file: Path to log file. If None, file logging is disabled.
        log_console: If True, also log to stderr.
    """
    global _logger
    level = getattr(logging, log_level.upper(), logging.INFO)
    handlers: list[logging.Handler] = []

    if log_console:
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        handlers.append(ch)

    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = Path.cwd() / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        handlers.append(fh)

    if not handlers:
        handlers.append(logging.NullHandler())

    logging.basicConfig(level=level, handlers=handlers, force=True)
    _logger = logging.getLogger("transtools")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name (typically __name__).

    Args:
        name: Logger name, usually module __name__.

    Returns:
        Logger instance under transtools.{name}.
    """
    return logging.getLogger(f"transtools.{name}")
