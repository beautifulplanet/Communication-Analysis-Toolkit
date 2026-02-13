"""
================================================================================
Communication Analysis Toolkit — Structured Logger
================================================================================

Configures structlog for JSON logging (production) or pretty printing (dev).
Replaces standard print() statements with structured events.
"""

import logging
import sys
from typing import Any

import structlog


def setup_logging(json_output: bool = False, verbose: bool = False) -> Any:
    """Configure structured logging.

    Args:
        json_output: If True, log in JSON format (good for parsing/Cloud).
        verbose: If True, set level to DEBUG.
    """

    # Set the level based on verbosity
    level = logging.DEBUG if verbose else logging.INFO

    # Standard library logging configuration (structlog wraps this)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if json_output:
        # JSON renderer for machine consumption
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console renderer for human readability
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,  # type: ignore
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


# Default logger instance
logger = structlog.get_logger()
