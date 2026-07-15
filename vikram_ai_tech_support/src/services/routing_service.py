"""Routing service: runs the manager agent and validates its decision.

The manager returns a structured ``RoutingDecision``. This service enforces
the confidence threshold (low-confidence answers become clarification
requests) and provides a small deterministic fallback used ONLY for error
recovery — never as the primary routing method.
"""

from __future__ import annotations

import time
from typing import Any, Protocol

from src.models.routing_models import RoutingDecision
from src.utils.exceptions import RoutingError
from src.utils.logging_config import get_logger
from src.utils.response_utils import build_task_prompt, extract_routing_decision

logger = get_logger(__name__)

DEFAULT_CLARIFICATION_QUESTION = (
    "Could you share a little more detail about your request — for example, "
    "is it about IT systems, finance, HR, office facilities, or a policy matter?"
)


class SupportsRun(Protocol):
    """Minimal protocol satisfied by AutoGen AssistantAgent (and test fakes)."""

    async def run(self, *, task: str) -> Any: ...


class RoutingService:
    """Classifies support requests via the manager agent."""

    def __init__(
        self,
        manager_agent: SupportsRun,
        confidence_threshold: float = 0.65,
        max_context_messages: int = 6,
    ) -> None:
        self._manager_agent = manager_agent
        self._confidence_threshold = confidence_threshold
        self._max_context_messages = max_context_messages

    async def route(
        self,
        user_query: str,
        conversation_context: list[dict[str, str]] | None = None,
    ) -> RoutingDecision:
        """Return a validated routing decision for ``user_query``.

        Raises:
            RoutingError: when the manager fails and recovery is impossible.
        """
        task = build_task_prompt(user_query, conversation_context, self._max_context_messages)
        started = time.perf_counter()
        try:
            result = await self._manager_agent.run(task=task)
            decision = extract_routing_decision(result)
        except RoutingError:
            # Invalid structured output: recover deterministically by asking
            # the user to clarify instead of guessing a department.
            logger.warning("Manager output invalid; falling back to clarification.")
            return self._fallback_decision()
        duration_ms = (time.perf_counter() - started) * 1000

        decision = self._apply_confidence_threshold(decision)
        logger.info(
            "Routing complete: department=%s confidence=%.2f "
            "needs_clarification=%s secondary=%s duration_ms=%.0f",
            decision.department,
            decision.confidence,
            decision.needs_clarification,
            decision.secondary_department,
            duration_ms,
        )
        return decision

    def _apply_confidence_threshold(self, decision: RoutingDecision) -> RoutingDecision:
        """Convert low-confidence routes into a clarification request."""
        if (
            decision.department != "Clarification"
            and not decision.needs_clarification
            and decision.confidence < self._confidence_threshold
        ):
            logger.info(
                "Confidence %.2f below threshold %.2f; requesting clarification.",
                decision.confidence,
                self._confidence_threshold,
            )
            return RoutingDecision(
                department="Clarification",
                confidence=decision.confidence,
                brief_reason="Routing confidence was too low to select a department.",
                needs_clarification=True,
                clarification_question=(
                    decision.clarification_question or DEFAULT_CLARIFICATION_QUESTION
                ),
            )
        if decision.needs_clarification and not decision.clarification_question:
            return decision.model_copy(
                update={"clarification_question": DEFAULT_CLARIFICATION_QUESTION}
            )
        return decision

    @staticmethod
    def _fallback_decision() -> RoutingDecision:
        """Deterministic error-recovery decision: ask the user to clarify."""
        return RoutingDecision(
            department="Clarification",
            confidence=0.0,
            brief_reason="The routing step could not be completed reliably.",
            needs_clarification=True,
            clarification_question=DEFAULT_CLARIFICATION_QUESTION,
        )
