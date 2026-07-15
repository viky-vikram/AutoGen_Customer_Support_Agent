"""Structured-output models used by the manager agent and the chat service."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Department = Literal["IT", "Finance", "HR", "Admin", "Compliance"]
RouteTarget = Literal["IT", "Finance", "HR", "Admin", "Compliance", "Clarification"]

DEPARTMENT_LABELS: dict[str, str] = {
    "IT": "IT Support",
    "Finance": "Finance Support",
    "HR": "Human Resources",
    "Admin": "Administration",
    "Compliance": "Compliance",
    "Clarification": "Clarification Needed",
}


class RoutingDecision(BaseModel):
    """The manager agent's structured classification of a support request."""

    department: RouteTarget
    confidence: float = Field(ge=0.0, le=1.0)
    brief_reason: str = Field(
        description="One short sentence explaining the routing choice. "
        "No hidden reasoning or step-by-step analysis."
    )
    needs_clarification: bool
    clarification_question: str | None = None
    secondary_department: Department | None = Field(
        default=None,
        description="Optional second department for cross-functional queries.",
    )


class SupportResponse(BaseModel):
    """Unified result returned by the chat service to the UI."""

    answer: str
    department: RouteTarget
    confidence: float = Field(ge=0.0, le=1.0)
    brief_reason: str = ""
    needs_clarification: bool = False
    clarification_question: str | None = None
    secondary_department: Department | None = None

    @property
    def department_label(self) -> str:
        return DEPARTMENT_LABELS.get(self.department, self.department)

    @property
    def confidence_percent(self) -> str:
        return f"{round(self.confidence * 100)}%"
