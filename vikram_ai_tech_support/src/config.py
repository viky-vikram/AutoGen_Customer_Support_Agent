"""Application configuration loaded from environment variables.

Uses ``python-dotenv`` to load a local ``.env`` file (never committed) and
validates every required value before any agent is created. The API key is
kept inside the config object and is never logged, printed, or displayed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

from src.utils.exceptions import ConfigurationError

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_CONFIDENCE_THRESHOLD = 0.65
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60.0
# How many recent conversation messages are replayed to agents as context.
DEFAULT_MAX_CONTEXT_MESSAGES = 6


@dataclass(frozen=True)
class AppConfig:
    """Validated, immutable application configuration."""

    openai_api_key: str = field(repr=False)
    model: str = DEFAULT_MODEL
    log_level: str = DEFAULT_LOG_LEVEL
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    max_context_messages: int = DEFAULT_MAX_CONTEXT_MESSAGES

    def __post_init__(self) -> None:
        if not isinstance(self.openai_api_key, str) or not self.openai_api_key.strip():
            raise ConfigurationError("OPENAI_API_KEY is missing or blank.")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ConfigurationError("OPENAI_MODEL must be a non-empty model name.")
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ConfigurationError(
                "ROUTING_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0."
            )


def load_config(dotenv_path: str | None = None) -> AppConfig:
    """Load and validate configuration from the environment / ``.env`` file.

    Raises:
        ConfigurationError: when a required value is missing or invalid.
    """
    load_dotenv(dotenv_path=dotenv_path, override=False)

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key.strip():
        raise ConfigurationError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.",
        )

    model = os.environ.get("OPENAI_MODEL", "").strip() or DEFAULT_MODEL
    log_level = os.environ.get("LOG_LEVEL", "").strip() or DEFAULT_LOG_LEVEL

    threshold_raw = os.environ.get("ROUTING_CONFIDENCE_THRESHOLD", "").strip()
    try:
        threshold = float(threshold_raw) if threshold_raw else DEFAULT_CONFIDENCE_THRESHOLD
    except ValueError as exc:
        raise ConfigurationError(
            "ROUTING_CONFIDENCE_THRESHOLD must be a number between 0.0 and 1.0."
        ) from exc

    return AppConfig(
        openai_api_key=api_key.strip(),
        model=model,
        log_level=log_level,
        confidence_threshold=threshold,
    )
