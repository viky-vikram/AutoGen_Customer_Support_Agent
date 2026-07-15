"""Conservative custom CSS for the Streamlit interface.

Static styling only — no user-provided content is ever interpolated into
this markup, so ``unsafe_allow_html`` is safe here.
"""

from __future__ import annotations

import streamlit as st

_CSS = """
<style>
/* Header banner */
.vat-header {
    background: linear-gradient(90deg, #1F4E79 0%, #2E6DA4 100%);
    color: #ffffff;
    padding: 1.1rem 1.5rem;
    border-radius: 0.6rem;
    margin-bottom: 0.75rem;
}
.vat-header h1 {
    color: #ffffff;
    font-size: 1.6rem;
    margin: 0 0 0.2rem 0;
    padding: 0;
}
.vat-header p {
    color: #dce9f5;
    margin: 0;
    font-size: 0.95rem;
}

/* Routing metadata badges shown above each answer */
.vat-badges { margin-bottom: 0.4rem; }
.vat-badge {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    margin-right: 0.4rem;
    border-radius: 1rem;
    font-size: 0.8rem;
    font-weight: 600;
    background-color: #EAF1F8;
    color: #1F4E79;
    border: 1px solid #B7C9DC;
}
.vat-badge.confidence { background-color: #E8F4EE; color: #2E6B4F; border-color: #BCD9C8; }
.vat-badge.clarify   { background-color: #FBEEE4; color: #A05A2C; border-color: #E4C4A8; }

/* Footer */
.vat-footer {
    text-align: center;
    color: #8a94a0;
    font-size: 0.8rem;
    padding-top: 1.5rem;
}
</style>
"""


def apply_custom_styles() -> None:
    """Inject the application's static CSS once per rerun."""
    st.markdown(_CSS, unsafe_allow_html=True)


def render_header() -> None:
    """Render the static company header banner."""
    st.markdown(
        """
        <div class="vat-header">
          <h1>🤖 Vikram AI Tech Support</h1>
          <p>Internal customer-support assistant — IT · Finance · HR ·
          Administration · Compliance</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer(model_name: str) -> None:
    """Render the static footer (model name is app config, not user input)."""
    st.markdown(
        f"""
        <div class="vat-footer">
          Vikram AI Tech · Internal use only · Powered by AutoGen AgentChat
          and {model_name} · Responses are guidance, not completed actions.
        </div>
        """,
        unsafe_allow_html=True,
    )
