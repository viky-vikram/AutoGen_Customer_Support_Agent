"""Chat orchestration: manager first, then exactly one department agent.

Flow (controlled, no free-form multi-agent conversation):

    user query -> input validation -> RoutingService (manager agent)
              -> clarification OR fixed-mapping lookup of one specialist
              -> specialist answer -> unified SupportResponse

The department-to-agent mapping is a fixed dictionary populated by the agent
factory; user input can never select an agent by name.
"""

from __future__ import annotations

import time

from src.config import AppConfig
from src.models.routing_models import RoutingDecision, SupportResponse
from src.services.routing_service import RoutingService, SupportsRun
from src.utils.exceptions import (
    AgentExecutionError,
    EmptyInputError,
    RoutingError,
)
from src.utils.logging_config import get_logger
from src.utils.response_utils import build_task_prompt, extract_final_text

logger = get_logger(__name__)

MAX_QUERY_LENGTH = 4000


class ChatService:
    """Orchestrates one support turn: route, then ask the selected specialist."""

    def __init__(
        self,
        routing_service: RoutingService,
        department_agents: dict[str, SupportsRun],
        max_context_messages: int = 6,
        model_client=None,
    ) -> None:
        self._routing_service = routing_service
        self._department_agents = dict(department_agents)
        self._max_context_messages = max_context_messages
        self._model_client = model_client  # owned; closed via aclose()

    @classmethod
    def from_config(cls, config: AppConfig) -> "ChatService":
        """Build a fully wired service (model client, manager, specialists)."""
        # Imported lazily so unit tests can use fakes without autogen installed.
        from src.agents.agent_factory import (
            create_department_agents,
            create_manager_agent,
            create_model_client,
        )

        model_client = create_model_client(config)
        routing_service = RoutingService(
            manager_agent=create_manager_agent(model_client),
            confidence_threshold=config.confidence_threshold,
            max_context_messages=config.max_context_messages,
        )
        return cls(
            routing_service=routing_service,
            department_agents=create_department_agents(model_client),
            max_context_messages=config.max_context_messages,
            model_client=model_client,
        )

    async def handle_user_query(
        self,
        user_query: str,
        conversation_context: list[dict[str, str]] | None = None,
    ) -> SupportResponse:
        """Process one user question and return the unified response.

        Raises:
            EmptyInputError: for empty / whitespace-only input.
            RoutingError: when routing fails irrecoverably.
            AgentExecutionError: when the selected specialist fails.
        """
        if not isinstance(user_query, str) or not user_query.strip():
            raise EmptyInputError("Rejected empty user query.")
        user_query = user_query.strip()[:MAX_QUERY_LENGTH]

        started = time.perf_counter()
        decision = await self._route(user_query, conversation_context)

        if decision.department == "Clarification" or decision.needs_clarification:
            logger.info("Returning clarification request; no specialist called.")
            return SupportResponse(
                answer=decision.clarification_question
                or "Could you provide more detail about your request?",
                department="Clarification",
                confidence=decision.confidence,
                brief_reason=decision.brief_reason,
                needs_clarification=True,
                clarification_question=decision.clarification_question,
            )

        answer = await self._ask_specialist(decision, user_query, conversation_context)
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "Turn complete: department=%s duration_ms=%.0f", decision.department, duration_ms
        )
        return SupportResponse(
            answer=answer,
            department=decision.department,
            confidence=decision.confidence,
            brief_reason=decision.brief_reason,
            needs_clarification=False,
            secondary_department=decision.secondary_department,
        )

    async def _route(
        self,
        user_query: str,
        conversation_context: list[dict[str, str]] | None,
    ) -> RoutingDecision:
        try:
            return await self._routing_service.route(user_query, conversation_context)
        except RoutingError:
            raise
        except Exception as exc:  # API, network, timeout, unexpected
            logger.exception("Manager agent failed: %s", exc.__class__.__name__)
            raise RoutingError(f"Manager agent failed: {exc.__class__.__name__}") from exc

    async def _ask_specialist(
        self,
        decision: RoutingDecision,
        user_query: str,
        conversation_context: list[dict[str, str]] | None,
    ) -> str:
        # Fixed-dictionary lookup only — never derived from raw user input.
        agent = self._department_agents.get(decision.department)
        if agent is None:
            logger.error("Unsupported route requested: %s", decision.department)
            raise RoutingError(f"Unsupported department: {decision.department}")

        task = build_task_prompt(user_query, conversation_context, self._max_context_messages)
        try:
            result = await agent.run(task=task)
            return extract_final_text(result)
        except Exception as exc:  # API, network, timeout, parsing, unexpected
            logger.exception(
                "Specialist '%s' failed: %s", decision.department, exc.__class__.__name__
            )
            raise AgentExecutionError(
                f"{decision.department} agent failed: {exc.__class__.__name__}"
            ) from exc

    async def aclose(self) -> None:
        """Release the model client if this service owns one."""
        if self._model_client is not None:
            try:
                await self._model_client.close()
            except Exception as exc:
                logger.warning("Model client close failed: %s", exc.__class__.__name__)
            finally:
                self._model_client = None
