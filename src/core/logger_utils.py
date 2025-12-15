"""Structured logging utilities using structlog."""

import logging
import sys
from typing import Any

import structlog
from rich.console import Console
from rich.logging import RichHandler

# Initialize rich console for better terminal output
console = Console()


def configure_logger(log_level: str = "INFO") -> None:
    """
    Configure structlog with rich formatting for better readability.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure standard logging
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                console=console,
                show_time=True,
                show_path=True,
            )
        ],
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str, log_level: str = "INFO") -> structlog.BoundLogger:
    """
    Get a configured structlog logger instance.
    
    Args:
        name: Name for the logger (usually __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        A configured structlog BoundLogger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting process", repo="pytorch/pytorch", stars=1000)
    """
    configure_logger(log_level)
    return structlog.get_logger(name)


# Create a default logger for the core module
logger = get_logger("moxi.core")
