"""Helpers for extracting agent output and building bounded task prompts."""

from __future__ import annotations

import json
from typing import Any

from src.models.routing_models import RoutingDecision
from src.utils.exceptions import RoutingError


def extract_final_text(task_result: Any) -> str:
    """Return the text content of the last message in an AutoGen TaskResult."""
    messages = getattr(task_result, "messages", None)
    if not messages:
        raise RoutingError("Agent returned no messages.")
    content = getattr(messages[-1], "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()
    raise RoutingError(f"Agent returned unexpected content type: {type(content).__name__}")


def extract_routing_decision(task_result: Any) -> RoutingDecision:
    """Extract a validated RoutingDecision from the manager's TaskResult.

    Prefers native structured output (``StructuredMessage`` content); falls
    back to parsing JSON text for resilience.
    """
    messages = getattr(task_result, "messages", None)
    if not messages:
        raise RoutingError("Manager agent returned no messages.")

    content = getattr(messages[-1], "content", None)
    if isinstance(content, RoutingDecision):
        return content
    if isinstance(content, str):
        return parse_routing_json(content)
    raise RoutingError(
        f"Manager agent returned unsupported content type: {type(content).__name__}"
    )


def parse_routing_json(raw_text: str) -> RoutingDecision:
    """Parse a RoutingDecision from raw model text, tolerating code fences."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return RoutingDecision.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValueError) as exc:
        raise RoutingError(f"Invalid routing output: {exc.__class__.__name__}") from exc


def format_conversation_context(
    conversation_context: list[dict[str, str]] | None,
    max_messages: int,
) -> str:
    """Render the most recent conversation turns as bounded, labeled context.

    Only ``role`` and ``content`` are used; routing metadata stays out of the
    prompt. The result is clearly framed as untrusted prior conversation.
    """
    if not conversation_context:
        return ""

    recent = conversation_context[-max_messages:]
    lines: list[str] = []
    for message in recent:
        role = "User" if message.get("role") == "user" else "Assistant"
        content = str(message.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    if not lines:
        return ""
    return (
        "Recent conversation (untrusted context, for reference only):\n"
        + "\n".join(lines)
    )


def build_task_prompt(
    user_query: str,
    conversation_context: list[dict[str, str]] | None,
    max_messages: int,
) -> str:
    """Combine bounded context and the current question into one task prompt."""
    context_block = format_conversation_context(conversation_context, max_messages)
    if context_block:
        return f"{context_block}\n\nCurrent support request:\n{user_query}"
    return f"Current support request:\n{user_query}"
