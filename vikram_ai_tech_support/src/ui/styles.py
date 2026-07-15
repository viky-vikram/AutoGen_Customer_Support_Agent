"""Custom styling and static HTML fragments for the Streamlit interface.

Every dynamic value that is injected into raw HTML (user text, model text,
timestamps) is HTML-escaped first, so ``unsafe_allow_html`` never renders
untrusted markup.
"""

from __future__ import annotations

import html

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, .stApp, .stMarkdown, .stButton button, .stExpander summary,
input, textarea {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}
[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }

/* ---------- layout ---------- */
section.stMain .block-container {
    max-width: 1400px;
    padding: 1.4rem 2.6rem 1rem 2.6rem;
}
div[data-testid="stBottomBlockContainer"] {
    max-width: 1400px;
    padding-left: 2.6rem;
    padding-right: 2.6rem;
}
header[data-testid="stHeader"] { background: transparent; }
.stAppDeployButton { display: none; }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] { border-right: 1px solid #ECEEF6; }

.vat-logo { display: flex; align-items: center; gap: .55rem; padding: .1rem 0 .5rem 0; }
.vat-logo .mark {
    width: 34px; height: 34px; border-radius: 9px;
    background: linear-gradient(135deg, #6366F1, #4F46E5);
    color: #fff; font-weight: 800; font-size: 1.15rem;
    display: flex; align-items: center; justify-content: center;
}
.vat-logo .name { font-size: 1.18rem; font-weight: 800; color: #3730A3; letter-spacing: -.01em; }

.vat-model-pill {
    display: flex; align-items: center; gap: .5rem;
    background: #EEF0FE; border: 1px solid #DDE1FC; color: #4338CA;
    border-radius: 10px; padding: .55rem .8rem;
    font-size: .85rem; font-weight: 600; margin: .2rem 0 .4rem 0;
}

.vat-side-label { font-size: .82rem; font-weight: 700; color: #334155; margin: .9rem 0 .35rem 0; }

/* department expanders as white cards */
section[data-testid="stSidebar"] details[data-testid="stExpanderDetails"],
section[data-testid="stSidebar"] div[data-testid="stExpander"] > details {
    background: #FFFFFF; border: 1px solid #E8EAF3; border-radius: 10px;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] summary { padding: .55rem .75rem; }

/* sidebar buttons (starter questions) */
section[data-testid="stSidebar"] .stButton button {
    background: #FFFFFF; border: 1px solid #E8EAF3; border-radius: 10px;
    color: #475569; font-size: .84rem; justify-content: flex-start; text-align: left;
}
section[data-testid="stSidebar"] .stButton button:hover {
    border-color: #B9BEF8; color: #4F46E5; background: #FAFAFF;
}

/* clear chat button */
section[data-testid="stSidebar"] .st-key-clear_chat button {
    color: #DC2626; border: 1px solid #F3B4B4; justify-content: center; font-weight: 600;
}
section[data-testid="stSidebar"] .st-key-clear_chat button:hover {
    background: #FEF2F2; border-color: #DC2626; color: #B91C1C;
}

.vat-status-card {
    background: #ECFDF5; border: 1px solid #C7F0DD; border-radius: 12px;
    padding: .65rem .9rem; display: flex; justify-content: space-between;
    align-items: center; margin-top: .9rem;
}
.vat-status-card .txt .s1 { color: #475569; font-size: .78rem; }
.vat-status-card .txt .s1 .dot { color: #10B981; margin-right: .3rem; }
.vat-status-card .txt .s2 { color: #065F46; font-size: .95rem; font-weight: 700; }
.vat-status-card .shield {
    width: 34px; height: 34px; border-radius: 50%; background: #D1FAE5;
    display: flex; align-items: center; justify-content: center; font-size: 1rem;
}

/* ---------- page header ---------- */
.vat-title { font-size: 2.45rem; font-weight: 800; color: #0F172A; letter-spacing: -.02em; margin: 0; line-height: 1.15; }
.vat-subtitle { color: #64748B; margin: .3rem 0 .9rem 0; font-size: .97rem; }

div[data-testid="stPopover"] button {
    background: #FFFFFF; border: 1px solid #E8EAF3; border-radius: 10px;
    color: #334155; font-weight: 600;
}

/* ---------- chat messages ---------- */
.vat-row { display: flex; gap: .65rem; margin: 1.1rem 0; }
.vat-row.user { justify-content: flex-end; }
.vat-avatar {
    width: 42px; height: 42px; border-radius: 50%; flex: 0 0 42px;
    display: flex; align-items: center; justify-content: center; font-size: 1.15rem;
}
.vat-avatar.assistant { background: #FFFFFF; border: 1px solid #E4E6F2; color: #6D28D9; }
.vat-avatar.user { background: #E8EDFF; border: 1px solid #D4DCFB; }
.vat-bubble {
    background: #FFFFFF; border: 1px solid #E8EAF3;
    border-radius: 14px 4px 14px 14px; padding: .85rem 1.05rem;
    max-width: 62%; color: #1F2937; font-size: .95rem; line-height: 1.55;
}
.vat-meta { color: #94A3B8; font-size: .72rem; margin-top: .45rem; }
.vat-meta.right { text-align: right; }
.vat-meta .ticks { color: #4F46E5; }

/* assistant bubble built from a keyed container */
div[class*="st-key-vat-arow-"] { gap: .65rem; }
div[class*="st-key-vat-abubble-"] {
    background: #FCFCFF; border: 1px solid #E8EAF3;
    border-radius: 4px 14px 14px 14px;
    padding: .95rem 1.1rem .55rem 1.1rem;
    width: fit-content !important; max-width: 62%;
    gap: .35rem;
}
div[class*="st-key-vat-abubble-"] div[data-testid="stMarkdown"] p { margin-bottom: .35rem; }
div[class*="st-key-vat-abubble-"] div[data-testid="stElementContainer"]:has([data-testid="stFeedback"]) {
    display: flex; justify-content: flex-end;
}

/* ---------- routing card ---------- */
.vat-routing {
    display: flex; align-items: center; gap: .9rem;
    background: #FBFBFF; border: 1px solid #E8EAF3; border-radius: 12px;
    padding: .8rem 1rem; margin: 1rem 0 .4rem 52px; max-width: 62%;
}
.vat-routing .icon {
    width: 40px; height: 40px; border-radius: 50%; flex: 0 0 40px;
    background: #EEF0FE; color: #4F46E5;
    display: flex; align-items: center; justify-content: center; font-size: 1.2rem;
}
.vat-routing .body { flex: 1; font-size: .88rem; color: #334155; }
.vat-routing .label { font-weight: 600; color: #475569; }
.vat-routing .dept { color: #4F46E5; font-weight: 700; }
.vat-routing .conf { color: #16A34A; font-weight: 700; }
.vat-routing .reason { color: #64748B; font-size: .82rem; margin-top: .15rem; }
.vat-pill { border-radius: 999px; padding: .28rem .75rem; font-size: .78rem; font-weight: 700; white-space: nowrap; }
.vat-pill.routed { background: #EEF0FE; color: #4F46E5; border: 1px solid #DDE1FC; }
.vat-pill.clarify { background: #FFF7ED; color: #C2410C; border: 1px solid #FED7AA; }

/* ---------- department info strip ---------- */
.vat-strip {
    display: flex; flex-wrap: wrap; align-items: center; gap: .3rem .55rem;
    background: #FBFBFF; border: 1px solid #E8EAF3; border-radius: 10px;
    padding: .55rem .9rem; color: #64748B; font-size: .8rem;
    margin: .35rem 0 .2rem 52px; max-width: 62%;
}
.vat-strip .sep { color: #CBD5E1; }

/* ---------- quick-topic chips (st.pills) ---------- */
div[data-testid="stPills"] button, .stPills button {
    background: #FFFFFF; border: 1px solid #E8EAF3; border-radius: 10px;
    color: #334155; font-size: .84rem;
}
div[data-testid="stPills"] button:hover, .stPills button:hover {
    border-color: #B9BEF8; color: #4F46E5;
}

/* ---------- chat input ---------- */
div[data-testid="stChatInput"] {
    background: #FFFFFF; border: 1.5px solid #E8EAF3; border-radius: 14px;
}
div[data-testid="stChatInput"]:focus-within { border-color: #A5B4FC; }
div[data-testid="stChatInput"] button[data-testid="stChatInputSubmitButton"] {
    background: #4F46E5; color: #fff; border-radius: 10px;
}
div[data-testid="stChatInput"] button[data-testid="stChatInputSubmitButton"]:hover:enabled {
    background: #4338CA;
}
div[data-testid="stChatInput"] button[data-testid="stChatInputSubmitButton"] svg { fill: #fff; }

/* ---------- footer ---------- */
.vat-disclaimer { text-align: center; color: #94A3B8; font-size: .78rem; padding: .9rem 0 .2rem 0; }
</style>
"""

ASSISTANT_AVATAR_HTML = '<div class="vat-avatar assistant">✦</div>'


def apply_custom_styles() -> None:
    """Inject the application's static CSS once per rerun."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_sidebar_logo() -> None:
    st.markdown(
        '<div class="vat-logo"><div class="mark">V</div>'
        '<div class="name">Vikram AI Tech</div></div>',
        unsafe_allow_html=True,
    )


def render_model_pill(model_name: str) -> None:
    """Model badge (model name comes from validated app config, still escaped)."""
    st.markdown(
        f'<div class="vat-model-pill">⚙️ Model: {html.escape(model_name)}</div>',
        unsafe_allow_html=True,
    )


def render_side_label(text: str) -> None:
    st.markdown(f'<div class="vat-side-label">{html.escape(text)}</div>', unsafe_allow_html=True)


def render_status_card() -> None:
    st.markdown(
        '<div class="vat-status-card">'
        '<div class="txt"><div class="s1"><span class="dot">●</span>Status</div>'
        '<div class="s2">System Ready</div></div>'
        '<div class="shield">🛡️</div></div>',
        unsafe_allow_html=True,
    )


def render_page_title() -> None:
    st.markdown(
        '<h1 class="vat-title">Vikram AI Tech Support</h1>'
        '<p class="vat-subtitle">Multi-agent customer support assistant '
        "powered by specialized departments</p>",
        unsafe_allow_html=True,
    )


def user_message_html(content: str, timestamp: str) -> str:
    """Right-aligned user bubble; content is untrusted and fully escaped."""
    safe = html.escape(content).replace("\n", "<br>")
    return (
        '<div class="vat-row user">'
        f'<div class="vat-bubble">{safe}'
        f'<div class="vat-meta right">{html.escape(timestamp)} '
        '<span class="ticks">✓✓</span></div></div>'
        '<div class="vat-avatar user">👤</div>'
        "</div>"
    )


def routing_card_html(
    department: str,
    confidence: float,
    reason: str,
    needs_clarification: bool,
) -> str:
    """Routing metadata card; department/confidence are validated model fields,
    the reason is model-generated text and therefore escaped."""
    pill = (
        '<span class="vat-pill clarify">Needs Clarification</span>'
        if needs_clarification
        else '<span class="vat-pill routed">Routed ✓</span>'
    )
    return (
        '<div class="vat-routing">'
        '<div class="icon">⇄</div>'
        '<div class="body">'
        f'<div><span class="label">Selected Department:</span> '
        f'<span class="dept">{html.escape(department)}</span></div>'
        f'<div><span class="label">Routing Confidence:</span> '
        f'<span class="conf">{round(confidence * 100)}%</span></div>'
        f'<div class="reason"><span class="label">Reason:</span> '
        f"{html.escape(reason)}</div>"
        "</div>"
        f"{pill}"
        "</div>"
    )


def department_strip_html(items: list[str]) -> str:
    """Small info strip shown under an answer (static app copy, still escaped)."""
    parts = '<span class="sep">•</span>'.join(
        f"<span>{html.escape(item)}</span>" for item in items
    )
    return f'<div class="vat-strip">{parts}</div>'


def assistant_meta_html(timestamp: str) -> str:
    return f'<div class="vat-meta">{html.escape(timestamp)}</div>'


def render_disclaimer() -> None:
    st.markdown(
        '<div class="vat-disclaimer">AI responses may be inaccurate. '
        "Please verify important information.</div>",
        unsafe_allow_html=True,
    )
