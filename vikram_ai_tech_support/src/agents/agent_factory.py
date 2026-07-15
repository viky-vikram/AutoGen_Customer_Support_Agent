"""Central factory for the shared model client and every AutoGen agent.

All agents are built through ``build_agent`` so that creation logic exists in
exactly one place. Department modules only declare their ``AgentSpec``.
The department-to-agent mapping is a fixed dictionary — user input can never
select an arbitrary agent or Python object.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.config import AppConfig
from src.models.routing_models import RoutingDecision
from src.prompts.system_prompts import MANAGER_SYSTEM_PROMPT
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# The OpenAI SDK re-serializes autogen's structured-output payloads, which
# triggers a harmless "Pydantic serializer warnings" UserWarning upstream.
warnings.filterwarnings(
    "ignore",
    message="Pydantic serializer warnings:",
    category=UserWarning,
    module="pydantic.main",
)


@dataclass(frozen=True)
class AgentSpec:
    """Declarative description of one department agent."""

    name: str
    description: str
    system_message: str


def create_model_client(config: AppConfig) -> OpenAIChatCompletionClient:
    """Create the single shared OpenAI model client used by all agents."""
    logger.info("Creating model client for model '%s'.", config.model)
    return OpenAIChatCompletionClient(
        model=config.model,
        api_key=config.openai_api_key,
        timeout=config.request_timeout_seconds,
    )


def build_agent(spec: AgentSpec, model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """Build one department AssistantAgent from its spec."""
    return AssistantAgent(
        name=spec.name,
        description=spec.description,
        system_message=spec.system_message,
        model_client=model_client,
    )


def create_manager_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """Build the routing manager agent with structured (Pydantic) output."""
    return AssistantAgent(
        name="manager_agent",
        description=(
            "Routing manager that classifies support requests into departments "
            "and returns a structured RoutingDecision. Never answers questions."
        ),
        system_message=MANAGER_SYSTEM_PROMPT,
        model_client=model_client,
        output_content_type=RoutingDecision,
    )


def create_department_agents(
    model_client: OpenAIChatCompletionClient,
) -> dict[str, AssistantAgent]:
    """Build all five department agents keyed by their routing department name.

    The mapping keys are fixed and match ``RoutingDecision.department`` values.
    """
    # Imported here to avoid circular imports (department modules use AgentSpec).
    from src.agents.admin_agent import ADMIN_AGENT_SPEC
    from src.agents.compliance_agent import COMPLIANCE_AGENT_SPEC
    from src.agents.finance_agent import FINANCE_AGENT_SPEC
    from src.agents.hr_agent import HR_AGENT_SPEC
    from src.agents.it_agent import IT_AGENT_SPEC

    specs: dict[str, AgentSpec] = {
        "IT": IT_AGENT_SPEC,
        "Finance": FINANCE_AGENT_SPEC,
        "HR": HR_AGENT_SPEC,
        "Admin": ADMIN_AGENT_SPEC,
        "Compliance": COMPLIANCE_AGENT_SPEC,
    }
    return {dept: build_agent(spec, model_client) for dept, spec in specs.items()}
