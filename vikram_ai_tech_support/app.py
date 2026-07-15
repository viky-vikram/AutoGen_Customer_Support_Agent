"""Vikram AI Tech Support — Streamlit entry point.

One conversation turn = one ChatService lifecycle: the manager agent routes
the question (structured output), exactly one department specialist answers,
and the shared model client is closed before the rerun ends.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="Vikram AI Tech Support",
    page_icon="🟣",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.config import AppConfig, load_config
from src.models.routing_models import SupportResponse
from src.services.chat_service import ChatService
from src.ui.styles import (
    ASSISTANT_AVATAR_HTML,
    apply_custom_styles,
    assistant_meta_html,
    department_strip_html,
    render_disclaimer,
    render_model_pill,
    render_page_title,
    render_side_label,
    render_sidebar_logo,
    render_status_card,
    routing_card_html,
    user_message_html,
)
from src.utils.async_utils import run_async
from src.utils.exceptions import ConfigurationError, SupportAppError
from src.utils.logging_config import get_logger, setup_logging

logger = get_logger("app")

WELCOME_MESSAGE = (
    "Hello! I'm Vikram AI Tech Support Assistant.\n\n"
    "I can help you with questions related to IT, Finance, HR, Admin, "
    "and Compliance.\n\n"
    "How can I assist you today?"
)

DEPARTMENT_INFO: dict[str, tuple[str, str]] = {
    "IT": (
        ":material/computer:",
        "Accounts, passwords, email, devices, software, VPN, network, "
        "printers, and application errors.",
    ),
    "Finance": (
        ":material/payments:",
        "Invoices, payments, reimbursements, expenses, budgets, payroll "
        "process, vendors, and purchase orders.",
    ),
    "HR": (
        ":material/group:",
        "Leave, attendance, benefits, recruitment, onboarding, reviews, "
        "workplace policies, and training.",
    ),
    "Admin": (
        ":material/domain:",
        "Facilities, meeting rooms, visitors, supplies, travel, maintenance, "
        "ID cards, and cafeteria.",
    ),
    "Compliance": (
        ":material/verified_user:",
        "Policies, data privacy, audits, ethics, conflicts of interest, "
        "records retention, and reporting.",
    ),
}

STARTER_QUESTIONS: list[str] = [
    "How do I reset my password?",
    "What is the leave policy?",
    "How do I submit an expense claim?",
    "Where can I find the IT helpdesk?",
]

QUICK_TOPIC_PROMPTS: dict[str, str] = {
    ":material/wifi: VPN issue": "I cannot connect to the company VPN.",
    ":material/event_available: Leave policy": "What is the process for applying for leave?",
    ":material/meeting_room: Meeting room booking": "How can I reserve a meeting room?",
    ":material/privacy_tip: Data privacy concern": "I need to report a possible data privacy violation.",
}

DEPARTMENT_STRIPS: dict[str, list[str]] = {
    "IT": [
        "🕘 IT helpdesk hours: Mon–Sat, 8:00 AM – 8:00 PM IST",
        "🛡️ Your data is secure and confidential",
        "🎧 Need more help? Contact IT Helpdesk",
    ],
    "Finance": [
        "🕘 Finance hours: Mon–Fri, 9:00 AM – 6:00 PM IST",
        "🛡️ Your data is secure and confidential",
        "🎧 Need more help? Contact Finance Team",
    ],
    "HR": [
        "🕘 HR hours: Mon–Fri, 9:00 AM – 6:00 PM IST",
        "🛡️ Your data is secure and confidential",
        "🎧 Need more help? Contact your HR Partner",
    ],
    "Admin": [
        "🕘 Admin desk hours: Mon–Sat, 8:00 AM – 8:00 PM IST",
        "🛡️ Your data is secure and confidential",
        "🎧 Need more help? Contact the Facilities Team",
    ],
    "Compliance": [
        "🕘 Compliance office hours: Mon–Fri, 9:00 AM – 6:00 PM IST",
        "🛡️ Your report is treated confidentially",
        "🎧 Need more help? Contact the Compliance Officer",
    ],
}


def _now() -> str:
    return datetime.now().strftime("%I:%M %p").lstrip("0")


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
    # The welcome card is the current empty-state prompt. Refresh its time
    # while there is no conversation so a long-lived Streamlit session cannot
    # display a stale timestamp after reruns or hot reloads.
    if not st.session_state.messages:
        st.session_state.welcome_time = _now()
    else:
        st.session_state.setdefault("welcome_time", _now())
    st.session_state.setdefault("chip_epoch", 0)


def render_sidebar(config: AppConfig) -> None:
    with st.sidebar:
        render_sidebar_logo()
        render_model_pill(config.model)

        render_side_label("Departments")
        for department, (icon, description) in DEPARTMENT_INFO.items():
            with st.expander(f"{icon} {department}"):
                st.write(description)

        render_side_label("Starter Questions")
        for question in STARTER_QUESTIONS:
            if st.button(
                question,
                key=f"starter_{question}",
                icon=":material/chat_bubble:",
                width="stretch",
            ):
                st.session_state.queued_prompt = question

        if st.button(
            "Clear Chat",
            key="clear_chat",
            icon=":material/delete:",
            width="stretch",
        ):
            st.session_state.messages = []
            st.session_state.pop("queued_prompt", None)
            st.session_state.welcome_time = _now()
            logger.info("Conversation cleared by user.")
            st.rerun()

        render_status_card()


def render_page_header() -> None:
    left, right = st.columns([0.78, 0.22], vertical_alignment="center")
    with left:
        render_page_title()
    with right:
        with st.popover(":material/history: Chat History", width="stretch"):
            if not st.session_state.messages:
                st.caption("No messages yet.")
            for message in st.session_state.messages[-20:]:
                who = "You" if message["role"] == "user" else "Assistant"
                snippet = message["content"][:90]
                if len(message["content"]) > 90:
                    snippet += "…"
                st.caption(f"**{who}** · {message.get('time', '')} — {snippet}")


def render_assistant_bubble(
    content: str,
    timestamp: str,
    idx: str,
    show_feedback: bool = True,
) -> None:
    """Assistant bubble: avatar + markdown content + timestamp + feedback."""
    with st.container(key=f"vat-arow-{idx}", horizontal=True, vertical_alignment="top"):
        st.markdown(ASSISTANT_AVATAR_HTML, unsafe_allow_html=True)
        with st.container(key=f"vat-acol-{idx}"):
            with st.container(key=f"vat-abubble-{idx}"):
                st.markdown(content)
            st.markdown(assistant_meta_html(timestamp), unsafe_allow_html=True)
            if show_feedback:
                st.feedback("thumbs", key=f"vat-fb-{idx}")


def render_assistant_turn(message: dict, idx: str) -> None:
    """Routing card, answer bubble, and department info strip for one answer."""
    department = message.get("department")
    if department:
        st.markdown(
            routing_card_html(
                department,
                message.get("confidence", 0.0),
                message.get("brief_reason", ""),
                message.get("needs_clarification", False),
            ),
            unsafe_allow_html=True,
        )
    render_assistant_bubble(message["content"], message.get("time", ""), idx)
    strip_items = DEPARTMENT_STRIPS.get(department or "")
    if strip_items and not message.get("needs_clarification"):
        st.markdown(department_strip_html(strip_items), unsafe_allow_html=True)


def render_history() -> None:
    render_assistant_bubble(
        WELCOME_MESSAGE, st.session_state.welcome_time, "welcome", show_feedback=False
    )
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(
                user_message_html(message["content"], message.get("time", "")),
                unsafe_allow_html=True,
            )
        else:
            render_assistant_turn(message, str(i))


def render_quick_topics() -> None:
    """Quick-topic chips above the input; selection queues a prompt."""
    epoch = st.session_state.chip_epoch
    choice = st.pills(
        "Quick topics",
        list(QUICK_TOPIC_PROMPTS),
        key=f"chips_{epoch}",
        label_visibility="collapsed",
    )
    if choice:
        st.session_state.queued_prompt = QUICK_TOPIC_PROMPTS[choice]
        st.session_state.chip_epoch += 1
        st.rerun()


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
    user_timestamp = _now()
    st.session_state.messages.append(
        {"role": "user", "content": user_query, "time": user_timestamp}
    )
    st.markdown(user_message_html(user_query, user_timestamp), unsafe_allow_html=True)

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

    assistant_message = {
        "role": "assistant",
        "content": response.answer,
        "time": _now(),
        "department": response.department,
        "confidence": response.confidence,
        "brief_reason": response.brief_reason,
        "needs_clarification": response.needs_clarification,
    }
    render_assistant_turn(assistant_message, f"live-{len(st.session_state.messages)}")
    st.session_state.messages.append(assistant_message)


def main() -> None:
    init_session_state()

    try:
        config = get_config()
    except ConfigurationError as exc:
        apply_custom_styles()
        render_page_title()
        st.error(exc.user_message)
        st.info(
            "Setup: copy `.env.example` to `.env`, add your OpenAI API key, "
            "then restart the app. See the README for details."
        )
        st.stop()
        return

    apply_custom_styles()
    render_sidebar(config)
    render_page_header()
    render_history()

    # New turn output renders here, below the history.
    turn_area = st.container()

    # Quick topics, input, and disclaimer live in the bottom-pinned bar,
    # exactly above/below the chat input like the design.
    with st.bottom:
        render_quick_topics()
        typed = st.chat_input(
            "Ask about IT, Finance, HR, Admin, or Compliance...",
            accept_file=True,
            file_type=None,
            submit_mode="disable",
        )
        render_disclaimer()

    typed_text = ""
    if typed:
        typed_text = (typed.text or "").strip()
        if typed.files:
            st.toast("📎 Attachments aren't processed yet — only your text is used.")

    queued = st.session_state.pop("queued_prompt", None)
    user_query = typed_text or (queued.strip() if queued else "")
    if user_query:
        with turn_area:
            handle_turn(config, user_query)


main()
