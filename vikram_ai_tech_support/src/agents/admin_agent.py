"""Administration department agent specification."""

from __future__ import annotations

from src.agents.agent_factory import AgentSpec
from src.prompts.system_prompts import ADMIN_SYSTEM_PROMPT

ADMIN_AGENT_SPEC = AgentSpec(
    name="admin_support_agent",
    description=(
        "Administration specialist for facilities, meeting rooms, visitor "
        "access, supplies, travel, maintenance, ID cards, and cafeteria."
    ),
    system_message=ADMIN_SYSTEM_PROMPT,
)
