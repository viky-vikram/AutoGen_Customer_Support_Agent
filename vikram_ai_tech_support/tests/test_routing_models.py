"""Validation tests for the structured routing and response models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models.routing_models import RoutingDecision, SupportResponse
from tests.conftest import make_decision


@pytest.mark.parametrize("department", ["IT", "Finance", "HR", "Admin", "Compliance"])
def test_valid_departments(department: str) -> None:
    decision = make_decision(department=department)
    assert decision.department == department


def test_clarification_is_a_valid_route() -> None:
    decision = make_decision(
        department="Clarification",
        needs_clarification=True,
        clarification_question="Which system are you referring to?",
    )
    assert decision.needs_clarification is True
    assert decision.clarification_question


@pytest.mark.parametrize("department", ["Legal", "Sales", "it", ""])
def test_invalid_department_rejected(department: str) -> None:
    with pytest.raises(ValidationError):
        make_decision(department=department)


def test_confidence_below_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        make_decision(confidence=-0.01)


def test_confidence_above_one_rejected() -> None:
    with pytest.raises(ValidationError):
        make_decision(confidence=1.01)


@pytest.mark.parametrize("confidence", [0.0, 0.65, 1.0])
def test_confidence_bounds_inclusive(confidence: float) -> None:
    assert make_decision(confidence=confidence).confidence == confidence


def test_secondary_department_optional() -> None:
    assert make_decision().secondary_department is None
    decision = make_decision(department="Finance", secondary_department="HR")
    assert decision.secondary_department == "HR"


def test_secondary_department_cannot_be_clarification() -> None:
    with pytest.raises(ValidationError):
        make_decision(secondary_department="Clarification")


def test_support_response_helpers() -> None:
    response = SupportResponse(answer="Hello", department="IT", confidence=0.943)
    assert response.department_label == "IT Support"
    assert response.confidence_percent == "94%"


def test_support_response_confidence_validated() -> None:
    with pytest.raises(ValidationError):
        SupportResponse(answer="x", department="IT", confidence=2.0)
