"""Chat-service orchestration tests with fake agents (no real API calls)."""

from __future__ import annotations

import pytest

from src.services.chat_service import ChatService
from src.services.routing_service import RoutingService
from src.utils.exceptions import (
    AgentExecutionError,
    EmptyInputError,
    RoutingError,
)
from tests.conftest import FakeAgent, FakeManagerAgent, make_decision


def build_service(
    decision=None,
    manager: FakeManagerAgent | None = None,
    departments: dict[str, FakeAgent] | None = None,
) -> tuple[ChatService, FakeManagerAgent, dict[str, FakeAgent]]:
    manager = manager or FakeManagerAgent(decision=decision or make_decision())
    departments = departments or {
        dept: FakeAgent(reply=f"{dept} specialist answer.")
        for dept in ("IT", "Finance", "HR", "Admin", "Compliance")
    }
    service = ChatService(
        routing_service=RoutingService(manager_agent=manager),
        department_agents=departments,
    )
    return service, manager, departments


async def test_correct_specialist_selected_and_only_one_called() -> None:
    service, manager, departments = build_service(
        decision=make_decision(department="Finance", confidence=0.92)
    )

    response = await service.handle_user_query("My reimbursement is pending.")

    assert response.department == "Finance"
    assert response.answer == "Finance specialist answer."
    assert response.confidence == 0.92
    assert len(manager.calls) == 1
    assert len(departments["Finance"].calls) == 1
    for dept in ("IT", "HR", "Admin", "Compliance"):
        assert departments[dept].calls == []


async def test_clarification_returned_without_calling_any_specialist() -> None:
    service, _, departments = build_service(
        decision=make_decision(
            department="Clarification",
            confidence=0.3,
            needs_clarification=True,
            clarification_question="Which system do you mean?",
        )
    )

    response = await service.handle_user_query("It does not work.")

    assert response.needs_clarification is True
    assert response.department == "Clarification"
    assert response.answer == "Which system do you mean?"
    assert all(agent.calls == [] for agent in departments.values())


async def test_unsupported_department_raises_routing_error() -> None:
    service, _, _ = build_service(
        decision=make_decision(department="HR"),
        departments={"IT": FakeAgent()},  # HR missing from the fixed mapping
    )

    with pytest.raises(RoutingError):
        await service.handle_user_query("How do I apply for leave?")


async def test_manager_failure_raises_routing_error() -> None:
    service, _, departments = build_service(
        manager=FakeManagerAgent(error=TimeoutError("simulated timeout"))
    )

    with pytest.raises(RoutingError) as exc_info:
        await service.handle_user_query("I cannot connect to the VPN.")

    assert exc_info.value.user_message  # safe user-facing message exists
    assert "simulated timeout" not in exc_info.value.user_message
    assert all(agent.calls == [] for agent in departments.values())


async def test_specialist_failure_raises_agent_execution_error() -> None:
    departments = {
        dept: FakeAgent() for dept in ("IT", "Finance", "HR", "Admin", "Compliance")
    }
    departments["IT"] = FakeAgent(error=ConnectionError("simulated network error"))
    service, _, _ = build_service(
        decision=make_decision(department="IT"), departments=departments
    )

    with pytest.raises(AgentExecutionError) as exc_info:
        await service.handle_user_query("My laptop will not start.")

    assert "simulated network error" not in exc_info.value.user_message


@pytest.mark.parametrize("bad_input", ["", "   ", "\n\t"])
async def test_empty_input_rejected_before_any_model_call(bad_input: str) -> None:
    service, manager, departments = build_service()

    with pytest.raises(EmptyInputError):
        await service.handle_user_query(bad_input)

    assert manager.calls == []
    assert all(agent.calls == [] for agent in departments.values())


async def test_conversation_context_passed_to_manager_and_specialist() -> None:
    service, manager, departments = build_service(
        decision=make_decision(department="IT")
    )
    context = [
        {"role": "user", "content": "My VPN keeps dropping."},
        {"role": "assistant", "content": "Try reconnecting to the office gateway."},
    ]

    response = await service.handle_user_query(
        "It still fails after that.", conversation_context=context
    )

    assert response.department == "IT"
    assert "My VPN keeps dropping." in manager.calls[0]
    assert "My VPN keeps dropping." in departments["IT"].calls[0]
    assert "It still fails after that." in departments["IT"].calls[0]


async def test_secondary_department_flows_into_response() -> None:
    service, _, _ = build_service(
        decision=make_decision(
            department="HR", confidence=0.8, secondary_department="Finance"
        )
    )

    response = await service.handle_user_query("How is unused leave paid out?")

    assert response.department == "HR"
    assert response.secondary_department == "Finance"


async def test_aclose_closes_owned_model_client() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    client = FakeClient()
    manager = FakeManagerAgent(decision=make_decision())
    service = ChatService(
        routing_service=RoutingService(manager_agent=manager),
        department_agents={},
        model_client=client,
    )

    await service.aclose()

    assert client.closed is True
