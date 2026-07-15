"""Configuration loading and validation tests (no .env file is read)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config import DEFAULT_CONFIDENCE_THRESHOLD, AppConfig, load_config
from src.utils.exceptions import ConfigurationError


@pytest.fixture()
def no_dotenv(tmp_path: Path) -> str:
    """A dotenv path that does not exist, so only real env vars apply."""
    return str(tmp_path / "does_not_exist.env")


def test_valid_configuration(clean_env, no_dotenv) -> None:
    clean_env.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    clean_env.setenv("OPENAI_MODEL", "gpt-4.1-mini")
    clean_env.setenv("LOG_LEVEL", "DEBUG")

    config = load_config(dotenv_path=no_dotenv)

    assert config.openai_api_key == "sk-test-not-a-real-key"
    assert config.model == "gpt-4.1-mini"
    assert config.log_level == "DEBUG"
    assert config.confidence_threshold == DEFAULT_CONFIDENCE_THRESHOLD


def test_missing_api_key_raises(clean_env, no_dotenv) -> None:
    with pytest.raises(ConfigurationError):
        load_config(dotenv_path=no_dotenv)


def test_empty_api_key_raises(clean_env, no_dotenv) -> None:
    clean_env.setenv("OPENAI_API_KEY", "   ")
    with pytest.raises(ConfigurationError):
        load_config(dotenv_path=no_dotenv)


def test_default_model_is_gpt_41_mini(clean_env, no_dotenv) -> None:
    clean_env.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    config = load_config(dotenv_path=no_dotenv)
    assert config.model == "gpt-4.1-mini"


def test_model_override_via_env(clean_env, no_dotenv) -> None:
    clean_env.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    clean_env.setenv("OPENAI_MODEL", "gpt-4.1")
    config = load_config(dotenv_path=no_dotenv)
    assert config.model == "gpt-4.1"


def test_invalid_threshold_raises(clean_env, no_dotenv) -> None:
    clean_env.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    clean_env.setenv("ROUTING_CONFIDENCE_THRESHOLD", "not-a-number")
    with pytest.raises(ConfigurationError):
        load_config(dotenv_path=no_dotenv)


def test_out_of_range_threshold_raises(clean_env, no_dotenv) -> None:
    clean_env.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    clean_env.setenv("ROUTING_CONFIDENCE_THRESHOLD", "1.5")
    with pytest.raises(ConfigurationError):
        load_config(dotenv_path=no_dotenv)


def test_api_key_not_in_repr() -> None:
    config = AppConfig(openai_api_key="sk-super-secret-value")
    assert "sk-super-secret-value" not in repr(config)


def test_blank_model_rejected() -> None:
    with pytest.raises(ConfigurationError):
        AppConfig(openai_api_key="sk-test-not-a-real-key", model="   ")
