"""Manager (router) agent definition.

The manager only classifies requests; it never writes departmental answers.
Its construction lives in the factory so the structured-output configuration
is defined in exactly one place.
"""

from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.agents.agent_factory import create_manager_agent

MANAGER_AGENT_NAME = "manager_agent"


def create_agent(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """Return the routing manager agent."""
    return create_manager_agent(model_client)
