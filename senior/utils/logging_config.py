"""
Logging Configuration
====================

Centralized logging setup for the project.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(
    name: str = "data_migration",
    level: int = logging.INFO,
    log_file: str = None,
    console: bool = True
) -> logging.Logger:
    """
    Setup a logger with consistent formatting.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        console: Whether to log to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        # Create logs directory if needed
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "data_migration") -> logging.Logger:
    """
    Get existing logger or create new one.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
