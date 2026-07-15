"""Centralized logging configuration.

All modules obtain loggers via ``get_logger(__name__)``. ``setup_logging`` is
idempotent so Streamlit reruns do not attach duplicate handlers.

Logging policy: log routing outcomes, durations, and exception types — never
API keys, tokens, passwords, or full user messages.
"""

from __future__ import annotations

import logging
import sys

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_CONFIGURED_FLAG = "_vikram_ai_tech_logging_configured"


def setup_logging(level: str = "INFO") -> None:
    """Configure the application root logger exactly once per process."""
    root = logging.getLogger("vikram_ai_tech")
    if getattr(root, _CONFIGURED_FLAG, False):
        root.setLevel(_resolve_level(level))
        return

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)
    root.setLevel(_resolve_level(level))
    root.propagate = False
    setattr(root, _CONFIGURED_FLAG, True)
    root.info("Logging initialized at level %s", level.upper())


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the application root logger."""
    return logging.getLogger(f"vikram_ai_tech.{name}")


def _resolve_level(level: str) -> int:
    resolved = logging.getLevelName(str(level).upper())
    return resolved if isinstance(resolved, int) else logging.INFO
