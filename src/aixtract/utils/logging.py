"""Logging configuration for AIXtract.

Adapted from CAMEL-AI (https://github.com/camel-ai/camel)
Copyright 2023-2026 @ CAMEL-AI.org. All Rights Reserved.
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import logging
import os
import sys

_logger = logging.getLogger("aixtract")


def _configure_library_logging() -> None:
    """Configure default logging for AIXtract."""
    if _logger.handlers:
        return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    _logger.addHandler(handler)
    _logger.setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name, prefixed with 'aixtract.'.

    Args:
        name: The name to append to 'aixtract.'.

    Returns:
        A logger instance with the name 'aixtract.{name}'.
    """
    return logging.getLogger(f"aixtract.{name}")


def set_log_level(level: str | int) -> None:
    """Set the logging level for AIXtract.

    Args:
        level: Logging level (e.g., 'DEBUG', 'INFO', logging.DEBUG).
    """
    _logger.setLevel(level)
    for handler in _logger.handlers:
        handler.setLevel(level)


if os.environ.get("AIXTRACT_LOGGING_DISABLED", "false").lower() != "true":
    _configure_library_logging()
