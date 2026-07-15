"""IT Support department agent specification."""

from __future__ import annotations

from src.agents.agent_factory import AgentSpec
from src.prompts.system_prompts import IT_SYSTEM_PROMPT

IT_AGENT_SPEC = AgentSpec(
    name="it_support_agent",
    description=(
        "IT Support specialist for account access, passwords, email, devices, "
        "software, VPN, network, printers, and application issues."
    ),
    system_message=IT_SYSTEM_PROMPT,
)
