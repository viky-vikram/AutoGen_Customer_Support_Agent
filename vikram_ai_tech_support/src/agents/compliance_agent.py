"""Compliance department agent specification."""

from __future__ import annotations

from src.agents.agent_factory import AgentSpec
from src.prompts.system_prompts import COMPLIANCE_SYSTEM_PROMPT

COMPLIANCE_AGENT_SPEC = AgentSpec(
    name="compliance_support_agent",
    description=(
        "Compliance specialist for internal policies, data privacy, audits, "
        "ethics, conflicts of interest, records retention, and reporting."
    ),
    system_message=COMPLIANCE_SYSTEM_PROMPT,
)
