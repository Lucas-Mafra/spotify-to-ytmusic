"""Logging setup shared by the whole application."""

from __future__ import annotations

import logging

DEFAULT_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging exactly once with a consistent format."""
    logging.basicConfig(level=level, format=DEFAULT_FORMAT)
