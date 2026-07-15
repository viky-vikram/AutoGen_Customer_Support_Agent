"""Finance Support department agent specification."""

from __future__ import annotations

from src.agents.agent_factory import AgentSpec
from src.prompts.system_prompts import FINANCE_SYSTEM_PROMPT

FINANCE_AGENT_SPEC = AgentSpec(
    name="finance_support_agent",
    description=(
        "Finance Support specialist for invoices, payments, reimbursements, "
        "expense claims, budgets, payroll process, vendors, and purchase orders."
    ),
    system_message=FINANCE_SYSTEM_PROMPT,
)
