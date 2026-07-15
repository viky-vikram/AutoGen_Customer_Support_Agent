"""Vikram AI Tech Support — Streamlit entry point.

One conversation turn = one ChatService lifecycle: the manager agent routes
the question (structured output), exactly one department specialist answers,
and the shared model client is closed before the rerun ends.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Vikram AI Tech Support",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.config import AppConfig, load_config
from src.models.routing_models import DEPARTMENT_LABELS, SupportResponse
from src.services.chat_service import ChatService
from src.ui.styles import apply_custom_styles, render_footer, render_header
from src.utils.async_utils import run_async
from src.utils.exceptions import ConfigurationError, SupportAppError
from src.utils.logging_config import get_logger, setup_logging

logger = get_logger("app")

DEPARTMENT_INFO: dict[str, str] = {
    "🖥️ IT Support": "Accounts, passwords, email, devices, software, VPN, "
                     "network, printers, application errors.",
    "💰 Finance": "Invoices, payments, reimbursements, expenses, budgets, "
                  "payroll process, vendors, purchase orders.",
    "👥 Human Resources": "Leave, attendance, benefits, recruitment, "
                          "onboarding, reviews, workplace policies, training.",
    "🏢 Administration": "Facilities, meeting rooms, visitors, supplies, "
                         "travel, maintenance, ID cards, cafeteria.",
    "⚖️ Compliance": "Policies, data privacy, audits, ethics, conflicts of "
                     "interest, records retention, reporting.",
}

STARTER_QUESTIONS: list[str] = [
    "I cannot connect to the company VPN.",
    "How do I submit a reimbursement request?",
    "What is the process for applying for leave?",
    "How can I reserve a meeting room?",
    "Where can I report a possible policy violation?",
]


@st.cache_resource(show_spinner=False)
def get_config() -> AppConfig:
    """Load and validate configuration once per server process."""
    setup_logging()
    config = load_config()
    setup_logging(config.log_level)
    logger.info("Application started with model '%s'.", config.model)
    return config


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_sidebar(config: AppConfig) -> None:
    with st.sidebar:
        st.subheader("Departments")
        for title, description in DEPARTMENT_INFO.items():
            with st.expander(title):
                st.write(description)

        st.divider()
        st.subheader("Try asking")
        for question in STARTER_QUESTIONS:
            if st.button(question, key=f"starter_{question}", width="stretch"):
                st.session_state.queued_prompt = question

        st.divider()
        st.caption(f"Model: `{config.model}`")
        st.caption(f"Messages in conversation: {len(st.session_state.messages)}")
        if st.button("🗑️ Clear conversation", type="primary", width="stretch"):
            st.session_state.messages = []
            st.session_state.pop("queued_prompt", None)
            logger.info("Conversation cleared by user.")
            st.rerun()


def render_routing_badges(department: str, confidence: float, clarification: bool) -> None:
    """Show department + confidence badges (values come from validated models)."""
    label = DEPARTMENT_LABELS.get(department, department)
    confidence_pct = f"{round(confidence * 100)}%"
    clarify_badge = (
        '<span class="vat-badge clarify">Needs clarification</span>' if clarification else ""
    )
    st.markdown(
        f'<div class="vat-badges">'
        f'<span class="vat-badge">Department: {label}</span>'
        f'<span class="vat-badge confidence">Routing confidence: {confidence_pct}</span>'
        f"{clarify_badge}</div>",
        unsafe_allow_html=True,
    )


def render_history() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and message.get("department"):
                render_routing_badges(
                    message["department"],
                    message.get("confidence", 0.0),
                    message.get("needs_clarification", False),
                )
            st.markdown(message["content"])


async def process_query(
    config: AppConfig,
    user_query: str,
    conversation_context: list[dict[str, str]],
) -> SupportResponse:
    """Run one full support turn, always releasing the model client."""
    service = ChatService.from_config(config)
    try:
        return await service.handle_user_query(user_query, conversation_context)
    finally:
        await service.aclose()


def handle_turn(config: AppConfig, user_query: str) -> None:
    # Context = prior conversation only (the current question is sent separately).
    context = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Routing your question to the right department..."):
                response = run_async(process_query(config, user_query, context))
        except SupportAppError as exc:
            logger.error("Turn failed: %s", exc.__class__.__name__)
            st.error(exc.user_message)
            return
        except Exception as exc:  # absolute last resort — never show a trace
            logger.exception("Unexpected error: %s", exc.__class__.__name__)
            st.error("An unexpected error occurred. Please try again in a moment.")
            return

        render_routing_badges(
            response.department, response.confidence, response.needs_clarification
        )
        st.markdown(response.answer)
        if response.secondary_department:
            st.caption(
                "This may also involve "
                f"{DEPARTMENT_LABELS.get(response.secondary_department)}."
            )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.answer,
            "department": response.department,
            "confidence": response.confidence,
            "needs_clarification": response.needs_clarification,
        }
    )


def main() -> None:
    init_session_state()

    try:
        config = get_config()
    except ConfigurationError as exc:
        apply_custom_styles()
        render_header()
        st.error(exc.user_message)
        st.info(
            "Setup: copy `.env.example` to `.env`, add your OpenAI API key, "
            "then restart the app. See the README for details."
        )
        st.stop()
        return

    apply_custom_styles()
    render_header()
    st.caption(
        "Ask a question and the manager agent will route it to the right "
        "department specialist. For urgent issues, contact the relevant team "
        "directly."
    )

    render_sidebar(config)
    render_history()

    queued = st.session_state.pop("queued_prompt", None)
    typed = st.chat_input("Type your support question here...", submit_mode="disable")
    user_query = typed or queued
    if user_query and user_query.strip():
        handle_turn(config, user_query.strip())

    render_footer(config.model)


main()
