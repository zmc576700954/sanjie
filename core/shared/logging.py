"""Logging utilities for agents_develop.

Provides a simple ``get_logger()`` factory that returns configured loggers
with a consistent format.
"""

from __future__ import annotations

import logging
from typing import Optional


_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(
    name: str,
    level: Optional[int] = None,
    fmt: Optional[str] = None,
) -> logging.Logger:
    """Return a configured logger with the given name.

    On the first call for a given *name* a ``StreamHandler`` is attached.
    Subsequent calls with the same *name* return the same logger instance
    without adding duplicate handlers.

    Args:
        name: Logger name (typically ``__name__`` of the calling module).
        level: Logging level. Defaults to ``logging.INFO``.
        fmt: Log message format string. Defaults to a standard format.

    Returns:
        A ``logging.Logger`` instance.
    """
    logger = logging.getLogger(name)

    if level is not None:
        logger.setLevel(level)
    elif not logger.handlers:
        logger.setLevel(logging.INFO)

    # Only add a handler if none exist yet (avoid duplicates on repeated calls)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(fmt or _DEFAULT_FORMAT, datefmt=_DEFAULT_DATE_FORMAT)
        )
        logger.addHandler(handler)

    return logger
