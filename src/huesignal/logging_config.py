"""Logging configuration for huesignal."""

import logging
import sys

# Logger for the application
logger = logging.getLogger("huesignal")


def setup_logging(verbose: bool = False, trace: bool = False) -> None:
    """
    Configure logging for the application.

    Args:
        verbose: Enable verbose logging (DEBUG level)
        trace: Enable trace logging with full tracebacks
    """
    # Remove any existing handlers
    logger.handlers.clear()

    # Create stderr handler (logs to stderr, not stdout)
    handler = logging.StreamHandler(sys.stderr)

    # Set log level based on verbosity
    if trace:
        log_level = logging.DEBUG
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    elif verbose:
        log_level = logging.DEBUG
        fmt = "%(levelname)s: %(message)s"
    else:
        log_level = logging.INFO
        fmt = "%(message)s"

    # Create formatter
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)

    # Configure logger
    logger.setLevel(log_level)
    logger.addHandler(handler)

    # Suppress noisy libraries
    if not trace:
        logging.getLogger("aiohttp").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger() -> logging.Logger:
    """Get the huesignal logger."""
    return logger
