"""Human Resources department agent specification."""

from __future__ import annotations

from src.agents.agent_factory import AgentSpec
from src.prompts.system_prompts import HR_SYSTEM_PROMPT

HR_AGENT_SPEC = AgentSpec(
    name="hr_support_agent",
    description=(
        "Human Resources specialist for leave, attendance, benefits, "
        "recruitment, onboarding, performance reviews, and workplace policies."
    ),
    system_message=HR_SYSTEM_PROMPT,
)
