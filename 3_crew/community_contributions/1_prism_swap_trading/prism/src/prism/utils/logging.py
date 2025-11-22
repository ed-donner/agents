# src/prism/utils/logging.py
"""Logging utilities for the application."""

import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log messages."""

    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[91m\033[1m",  # Bold Red
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        """Format the log message with colors based on the log level."""
        log_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, '')}{log_message}{self.COLORS['RESET']}"


def setup_logger(name: str = "prism", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger with colored output.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance

    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Create formatter
    formatter = ColoredFormatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger if not already added
    if not logger.handlers:
        logger.addHandler(console_handler)

    # Prevent propagation to the root logger
    logger.propagate = False

    return logger


# Create and export default logger instance
logger = setup_logger()


def set_log_level(level: str) -> None:
    """Set the logging level for the default logger.

    Args:
        level: Logging level string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    logger.setLevel(numeric_level)
    for handler in logger.handlers:
        handler.setLevel(numeric_level)
