"""Shared test fixtures and fakes.

No test in this suite makes a real OpenAI API call: agents are replaced by
lightweight fakes that mimic AutoGen's ``run(task=...)`` / TaskResult shape.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.routing_models import RoutingDecision  # noqa: E402


@dataclass
class FakeMessage:
    content: Any


@dataclass
class FakeTaskResult:
    messages: list[FakeMessage]


@dataclass
class FakeAgent:
    """Mimics AssistantAgent.run(task=...) and records every call."""

    reply: Any = "This is a fake specialist answer."
    error: Exception | None = None
    calls: list[str] = field(default_factory=list)

    async def run(self, *, task: str) -> FakeTaskResult:
        self.calls.append(task)
        if self.error is not None:
            raise self.error
        return FakeTaskResult(messages=[FakeMessage(content=self.reply)])


@dataclass
class FakeManagerAgent:
    """Returns a canned RoutingDecision, simulating structured model output."""

    decision: RoutingDecision | None = None
    raw_reply: Any = None  # used instead of `decision` when set (e.g. bad JSON)
    error: Exception | None = None
    calls: list[str] = field(default_factory=list)

    async def run(self, *, task: str) -> FakeTaskResult:
        self.calls.append(task)
        if self.error is not None:
            raise self.error
        content = self.raw_reply if self.raw_reply is not None else self.decision
        return FakeTaskResult(messages=[FakeMessage(content=content)])


def make_decision(**overrides: Any) -> RoutingDecision:
    """Build a valid RoutingDecision with sensible defaults."""
    defaults: dict[str, Any] = {
        "department": "IT",
        "confidence": 0.95,
        "brief_reason": "Test routing decision.",
        "needs_clarification": False,
        "clarification_question": None,
        "secondary_department": None,
    }
    defaults.update(overrides)
    return RoutingDecision(**defaults)


@pytest.fixture()
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Remove all app environment variables so tests fully control them."""
    for var in (
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "LOG_LEVEL",
        "ROUTING_CONFIDENCE_THRESHOLD",
    ):
        monkeypatch.delenv(var, raising=False)
    return monkeypatch
