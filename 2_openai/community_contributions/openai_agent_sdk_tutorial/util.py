import logging
from typing import Optional


def configure_logging(
    level: str = "INFO",
    format: Optional[str] = None,
    datefmt: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure logging for this application.

    This function configures the root logger to capture logs from all modules
    (app, hooks, tools) regardless of how they're imported.

    Args:
        level: Log level as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to "INFO".
        format: Optional custom format string for log messages.
                If not provided, uses a default format with timestamp and level.
        datefmt: Optional custom date format string.
        log_file: Optional path to a log file. If provided, logs are written to the file
                  instead of the console.

    Examples:
    ::

        Basic usage - set log level to DEBUG:
        >>> from .utils import configure_logging
        >>> configure_logging(level="DEBUG")

        Log to a file:
        >>> configure_logging(level="DEBUG", log_file="app.log")

        Custom format:
        >>> configure_logging(
        ...     level="INFO",
        ...     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        ...     datefmt="%Y-%m-%d %H:%M:%S"
        ... )
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Suppress noisy third-party loggers
    logging.getLogger("mcp").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

    # Configure root logger to catch all application logs
    # This works regardless of how modules are imported (__main__, hooks, tools, etc.)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Only add handler if root doesn't have one (avoid duplicate logs)
    if not root_logger.handlers:
        handler: logging.Handler
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()
        handler.setLevel(log_level)
        handler.setFormatter(
            logging.Formatter(
                format or "%(asctime)s %(levelname)-8s %(name)s - %(message)s",
                datefmt=datefmt or "%Y-%m-%d %H:%M:%S",
            )
        )
        root_logger.addHandler(handler)
