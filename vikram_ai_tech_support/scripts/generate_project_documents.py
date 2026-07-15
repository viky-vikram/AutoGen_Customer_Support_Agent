"""Generate all project documents for Vikram AI Tech Support.

Produces, inside the ``data/`` folder:
  - development_plan.pdf   (ReportLab, multi-page, numbered)
  - workflow_chart.png     (matplotlib, no system executables required)
  - workflow_chart.mmd     (editable Mermaid source)

Run from the project root:

    python scripts/generate_project_documents.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib

matplotlib.use("Agg")  # headless rendering; no display or system tools needed

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.utils.exceptions import DocumentGenerationError
from src.utils.logging_config import get_logger, setup_logging

logger = get_logger("scripts.generate_project_documents")

COMPANY = "Vikram AI Tech"
PROJECT = "Multi-Agent Customer Support Chatbot"
DATA_DIR = PROJECT_ROOT / "data"

ACCENT = colors.HexColor("#1F4E79")
LIGHT = colors.HexColor("#EAF1F8")

DEPARTMENTS = ["IT", "Finance", "HR", "Admin", "Compliance"]


# --------------------------------------------------------------------------
# PDF: development plan
# --------------------------------------------------------------------------

def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontSize=26, leading=32,
            textColor=ACCENT, spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "CoverSubtitle", parent=base["Title"], fontSize=15, leading=20,
            textColor=colors.HexColor("#444444"),
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontSize=15, leading=19,
            textColor=ACCENT, spaceBefore=14, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontSize=12, leading=15,
            textColor=colors.HexColor("#2E6DA4"), spaceBefore=8, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontSize=10, leading=14,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base["BodyText"], fontSize=10, leading=14,
            leftIndent=14, bulletIndent=4, spaceAfter=3,
        ),
        "mono": ParagraphStyle(
            "Mono", parent=base["Code"], fontSize=8, leading=10.5,
            leftIndent=8, backColor=LIGHT, borderPadding=6, spaceAfter=8,
        ),
    }


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.2 * cm, f"{COMPANY} — Development Plan")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def _bullets(styles, items: list[str]) -> list[Paragraph]:
    return [Paragraph(item, styles["bullet"], bulletText="•") for item in items]


def _section(styles, number: int, heading: str, flowables: list) -> list:
    return [Paragraph(f"{number}. {heading}", styles["h1"]), *flowables]


def generate_development_plan_pdf(output_path: Path) -> Path:
    """Build the multi-page development-plan PDF with ReportLab."""
    styles = _styles()
    story: list = []

    # ---- 1. Cover page -----------------------------------------------------
    story.extend([
        Spacer(1, 4.5 * cm),
        Paragraph(PROJECT, styles["title"]),
        Paragraph(COMPANY, styles["subtitle"]),
        Spacer(1, 1.2 * cm),
        Table(
            [
                ["Document", "Development Plan"],
                ["Purpose", "Design, build, test, and deployment plan for the "
                            "multi-agent internal customer-support chatbot."],
                ["Technology stack", "Python 3.10+, Microsoft AutoGen AgentChat, "
                                     "Streamlit, OpenAI gpt-4.1-mini, Pydantic, "
                                     "ReportLab, Matplotlib, Pytest"],
                ["Date", date.today().isoformat()],
                ["Status", "Approved for implementation"],
            ],
            colWidths=[4 * cm, 11.5 * cm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("TEXTCOLOR", (0, 0), (0, -1), ACCENT),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B7C9DC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]),
        ),
        PageBreak(),
    ])

    body = styles["body"]

    # ---- 2. Executive summary ---------------------------------------------
    story += _section(styles, 2, "Executive Summary", [
        Paragraph(
            f"{COMPANY} will deploy an internal first-level customer-support "
            "chatbot built on Microsoft AutoGen AgentChat. A manager agent "
            "classifies each employee request with a structured, validated "
            "routing decision, then exactly one of five department agents "
            "(IT, Finance, HR, Administration, Compliance) answers it. The "
            "Streamlit interface shows the selected department, the routing "
            "confidence, and the specialist's answer, and asks a clarifying "
            "question when a request is ambiguous.", body),
        Paragraph(
            "The system deliberately avoids free-form multi-agent chatter: the "
            "orchestration is a controlled two-step pipeline that is cheap, "
            "predictable, testable, and resistant to prompt injection.", body),
    ])

    # ---- 3. Business objective ----------------------------------------------
    story += _section(styles, 3, "Business Objective", _bullets(styles, [
        "Reduce first-response time for internal support requests to seconds.",
        "Deflect routine questions from IT, Finance, HR, Admin, and Compliance staff.",
        "Route every request to the correct department on the first attempt.",
        "Provide safe, policy-aware guidance that never claims to perform actions "
        "the system cannot actually perform.",
        "Create a foundation for future integration with ticketing and HRIS tools.",
    ]))

    # ---- 4. Functional scope -------------------------------------------------
    story += _section(styles, 4, "Functional Scope", _bullets(styles, [
        "Chat interface with persistent per-session conversation history and a "
        "clear-conversation control.",
        "Structured routing (department, confidence, reason, clarification flag, "
        "optional secondary department) validated with Pydantic.",
        "Clarification loop for ambiguous or low-confidence requests "
        "(threshold 0.65).",
        "Department indicator and confidence indicator on every answer.",
        "Starter questions, department descriptions, and model info in the sidebar.",
        "Out of scope for v1: real system integrations (password resets, bookings, "
        "approvals), authentication, persistence beyond the browser session.",
    ]))

    # ---- 5. Agent architecture -----------------------------------------------
    agent_rows = [
        ["Agent", "Role", "Key boundaries"],
        ["manager_agent", "Classifies each request and returns a structured "
         "RoutingDecision; detects ambiguity and cross-functional requests.",
         "Never answers questions; never follows user routing instructions."],
        ["it_support_agent", "Accounts, passwords, email, devices, software, "
         "VPN, network, printers, application errors.",
         "Guidance only; never requests or reveals secrets."],
        ["finance_support_agent", "Invoices, payments, reimbursements, expenses, "
         "budgets, payroll process, vendors, purchase orders.",
         "No investment/tax/legal advice; cannot approve or pay."],
        ["hr_support_agent", "Leave, attendance, benefits, recruitment, "
         "onboarding, reviews, workplace policy, training.",
         "Careful with personal data; cannot approve leave or change records."],
        ["admin_support_agent", "Facilities, meeting rooms, visitors, supplies, "
         "travel, maintenance, ID cards, cafeteria.",
         "Explains request processes; cannot book or reserve."],
        ["compliance_support_agent", "Policies, data privacy, audits, ethics, "
         "conflicts of interest, records retention, reporting.",
         "Not legal advice; escalates serious concerns to official channels."],
    ]
    story += _section(styles, 5, "Agent Architecture", [
        Table(
            [[Paragraph(c, ParagraphStyle("cell", parent=body, fontSize=8.5,
                                          leading=11)) for c in row]
             for row in agent_rows],
            colWidths=[3.6 * cm, 6.2 * cm, 5.7 * cm],
            repeatRows=1,
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B7C9DC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
    ])

    # ---- 6. End-to-end workflow ------------------------------------------------
    story += _section(styles, 6, "End-to-End Workflow", [
        Preformatted(
            "User\n"
            "  v\n"
            "Streamlit Chat UI  (st.chat_input)\n"
            "  v\n"
            "Input Validation   (reject empty / oversized input)\n"
            "  v\n"
            "Manager Agent      (gpt-4.1-mini, structured output)\n"
            "  v\n"
            "RoutingDecision    (Pydantic validation + 0.65 threshold)\n"
            "  |-- ambiguous --> Clarification question back to the user\n"
            "  v\n"
            "Selected Department Agent (exactly one of IT / Finance / HR /\n"
            "                           Admin / Compliance)\n"
            "  v\n"
            "Final Response     (department + confidence + answer)\n"
            "  v\n"
            "Conversation History (st.session_state.messages)",
            styles["mono"],
        ),
    ])

    # ---- 7. Technical architecture ----------------------------------------------
    story += _section(styles, 7, "Technical Architecture", _bullets(styles, [
        "<b>UI layer</b> — Streamlit app (app.py) with chat components, sidebar, "
        "session-state history, and conservative custom CSS.",
        "<b>Service layer</b> — ChatService orchestrates one turn; "
        "RoutingService wraps the manager agent and enforces the confidence "
        "threshold and error-recovery fallback.",
        "<b>Agent layer</b> — AutoGen AssistantAgent instances built by a "
        "central factory sharing one OpenAIChatCompletionClient.",
        "<b>Models</b> — Pydantic RoutingDecision (structured output) and "
        "SupportResponse (unified UI contract).",
        "<b>Configuration</b> — python-dotenv + validated AppConfig; the API "
        "key never appears in code, logs, or the UI.",
        "<b>Async bridge</b> — run_async() executes AutoGen coroutines safely "
        "from Streamlit's synchronous script thread.",
    ]))

    # ---- 8. Folder structure --------------------------------------------------
    story += _section(styles, 8, "Folder Structure", [
        Preformatted(
            "vikram_ai_tech_support/\n"
            "|- app.py                     Streamlit entry point\n"
            "|- README.md / requirements.txt / .env.example / .gitignore\n"
            "|- src/\n"
            "|  |- config.py               validated environment configuration\n"
            "|  |- agents/                 factory + manager + 5 department agents\n"
            "|  |- models/routing_models.py  structured routing / response models\n"
            "|  |- prompts/system_prompts.py all agent system messages\n"
            "|  |- services/               chat_service.py, routing_service.py\n"
            "|  |- ui/styles.py            conservative custom CSS\n"
            "|  |- utils/                  async, exceptions, logging, parsing\n"
            "|- scripts/generate_project_documents.py\n"
            "|- data/                      development_plan.pdf, workflow chart\n"
            "|- tests/                     pytest suite (no real API calls)",
            styles["mono"],
        ),
        PageBreak(),
    ])

    # ---- 9. Implementation phases ----------------------------------------------
    story += _section(styles, 9, "Implementation Phases", _bullets(styles, [
        "<b>Phase 1 — Foundation:</b> configuration, logging, exceptions, "
        "folder structure, environment templates.",
        "<b>Phase 2 — Models and prompts:</b> RoutingDecision, SupportResponse, "
        "all system prompts with security rules.",
        "<b>Phase 3 — Agents:</b> agent factory, manager with structured "
        "output, five department agents.",
        "<b>Phase 4 — Services:</b> routing service (threshold + fallback) and "
        "chat orchestration with full error handling.",
        "<b>Phase 5 — UI:</b> Streamlit chat interface, sidebar, indicators, "
        "clear-chat, starter questions.",
        "<b>Phase 6 — Documentation and QA:</b> PDF/chart generation, README, "
        "automated tests, security review.",
    ]))

    # ---- 10. Development milestones ---------------------------------------------
    milestone_rows = [
        ["Milestone", "Deliverable", "Exit criterion"],
        ["M1", "Config + utilities", "Config validation tests pass"],
        ["M2", "Routing models + prompts", "Model validation tests pass"],
        ["M3", "Agents + factory", "All six agents build from one factory"],
        ["M4", "Services", "Routing and chat-service tests pass with fakes"],
        ["M5", "Streamlit UI", "Smoke test: app starts and completes a turn"],
        ["M6", "Docs + hardening", "PDF/PNG/MMD generated; full suite green"],
    ]
    story += _section(styles, 10, "Development Milestones", [
        Table(
            milestone_rows,
            colWidths=[1.8 * cm, 6.2 * cm, 7.5 * cm],
            repeatRows=1,
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B7C9DC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]),
        ),
    ])

    # ---- 11. Testing strategy -----------------------------------------------------
    story += _section(styles, 11, "Testing Strategy", _bullets(styles, [
        "Unit tests for configuration validation (missing/blank key, default "
        "model gpt-4.1-mini).",
        "Model tests for RoutingDecision bounds, literals, and optional fields.",
        "Routing-service tests with fake manager agents covering all five "
        "departments, clarification, low confidence, and prompt injection.",
        "Chat-service tests proving exactly one specialist is called, "
        "clarification short-circuits, and every failure mode maps to a "
        "typed exception.",
        "Document tests validating the PDF signature, PNG signature, and "
        "Mermaid content.",
        "No test makes a real OpenAI API call; all model interaction is faked.",
    ]))

    # ---- 12. Security and privacy ---------------------------------------------------
    story += _section(styles, 12, "Security and Privacy Considerations", _bullets(styles, [
        "API key only in .env (git-ignored); validated at startup; never "
        "logged, printed, or shown in the UI.",
        "Every agent carries prompt-injection resistance rules: role "
        "retention, untrusted user content, no prompt disclosure, no secrets.",
        "The manager classifies by business intent and ignores user-supplied "
        "routing instructions.",
        "Fixed department-to-agent dictionary; user input can never select an "
        "arbitrary agent or Python object; no eval/exec/shell execution.",
        "Agents never claim to have completed actions (resets, approvals, "
        "bookings) and never request passwords, OTPs, or tokens.",
        "Logs record routing metadata and exception types, not full user "
        "messages or any credentials; transcripts are not written to disk.",
    ]))

    # ---- 13. Error-handling strategy ---------------------------------------------------
    story += _section(styles, 13, "Error-Handling Strategy", _bullets(styles, [
        "Typed exceptions (ConfigurationError, EmptyInputError, RoutingError, "
        "AgentExecutionError, DocumentGenerationError) each carry a safe "
        "user-facing message.",
        "Invalid structured output from the manager degrades deterministically "
        "to a clarification request instead of a wrong route.",
        "API, rate-limit, network, and timeout errors are caught at the "
        "service boundary, logged with technical detail, and surfaced to the "
        "user as friendly messages without stack traces.",
        "Empty input is rejected before any model call is made.",
    ]))

    # ---- 14. Deployment plan ---------------------------------------------------
    story += _section(styles, 14, "Deployment Plan", _bullets(styles, [
        "v1 runs locally or on an internal VM: create a virtual environment, "
        "install requirements.txt, provide .env, run 'streamlit run app.py'.",
        "Recommended next step: containerize with a slim Python base image and "
        "deploy behind the company SSO reverse proxy.",
        "Secrets provided via environment variables or a secret manager — "
        "never baked into the image or repository.",
        "Log level configurable via LOG_LEVEL; INFO in production.",
    ]))

    # ---- 15. Risks and mitigations ------------------------------------------------
    risk_rows = [
        ["Risk", "Impact", "Mitigation"],
        ["Misrouted requests", "Wrong department answers",
         "Structured output, 0.65 confidence threshold, clarification loop"],
        ["Hallucinated company policy", "Employees act on wrong info",
         "Prompts forbid invented policy; agents state when policy is unknown"],
        ["Prompt injection", "Role or routing manipulation",
         "Shared security rules; intent-based routing; fixed agent mapping"],
        ["API outage / rate limits", "Support unavailable",
         "Typed error handling, friendly retry messaging, timeouts"],
        ["Secret leakage", "Credential compromise",
         ".env git-ignored, no logging of secrets, placeholder-only examples"],
        ["Cost growth", "Budget overrun",
         "gpt-4.1-mini, bounded context window, exactly two calls per turn"],
    ]
    story += _section(styles, 15, "Risks and Mitigations", [
        Table(
            [[Paragraph(c, ParagraphStyle("cell2", parent=body, fontSize=8.5,
                                          leading=11)) for c in row]
             for row in risk_rows],
            colWidths=[4.2 * cm, 4.4 * cm, 6.9 * cm],
            repeatRows=1,
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B7C9DC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]),
        ),
    ])

    # ---- 16. Definition of done ------------------------------------------------
    story += _section(styles, 16, "Definition of Done", _bullets(styles, [
        "The app starts with 'streamlit run app.py' and completes a routed "
        "conversation turn end to end.",
        "Six agents exist; the manager runs before every specialist; only the "
        "selected specialist answers.",
        "Ambiguous questions yield a clarification request; history and "
        "clear-chat work.",
        "development_plan.pdf, workflow_chart.png, and workflow_chart.mmd are "
        "valid, readable, and regenerable from one script.",
        "The full pytest suite passes without real API calls; no secrets in "
        "the repository; README instructions match the implementation.",
    ]))

    # ---- 17. Future enhancements ------------------------------------------------
    story += _section(styles, 17, "Future Enhancements", _bullets(styles, [
        "Real tool integrations: ticket creation, room booking, leave-balance "
        "lookup via authenticated APIs.",
        "SSO authentication and per-user conversation persistence.",
        "Retrieval over the real company policy library (RAG) to ground "
        "answers in actual documents.",
        "Feedback buttons and routing-quality analytics dashboards.",
        "Multi-language support and voice input.",
        "Human-handoff escalation directly into the ticketing system.",
    ]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        title=f"{COMPANY} — {PROJECT} Development Plan",
        author=COMPANY,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    logger.info("Development plan written to %s", output_path)
    return output_path


# --------------------------------------------------------------------------
# Workflow chart (PNG via matplotlib — pure Python, no Graphviz needed)
# --------------------------------------------------------------------------

def _draw_box(ax, x, y, w, h, text, facecolor, fontsize=11, textcolor="white"):
    box = mpatches.FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.4, edgecolor="#1F4E79", facecolor=facecolor,
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=textcolor, fontweight="bold", zorder=5)


def _draw_arrow(ax, x1, y1, x2, y2, color="#1F4E79", style="-|>", lw=1.8,
                connection="arc3,rad=0.0", dashed=False):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops={
            "arrowstyle": style, "color": color, "lw": lw,
            "linestyle": "--" if dashed else "-",
            "connectionstyle": connection, "shrinkA": 2, "shrinkB": 2,
        },
        zorder=3,
    )


def generate_workflow_chart_png(output_path: Path) -> Path:
    """Draw the routing workflow as a readable PNG with matplotlib."""
    fig, ax = plt.subplots(figsize=(14, 11), dpi=150)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 13)
    ax.axis("off")

    fig.suptitle(
        f"{COMPANY} — Multi-Agent Customer Support Workflow",
        fontsize=18, fontweight="bold", color="#1F4E79", y=0.97,
    )

    dark, mid, dept_color, light = "#1F4E79", "#2E6DA4", "#3E8E7E", "#EAF1F8"
    cx = 7.0

    # Main vertical pipeline
    _draw_box(ax, cx, 12.0, 3.4, 0.75, "User", dark)
    _draw_box(ax, cx, 10.7, 3.8, 0.75, "Streamlit Chat UI", mid)
    _draw_box(ax, cx, 9.4, 3.8, 0.75, "Input Validation", mid)
    _draw_box(ax, cx, 8.1, 3.8, 0.75, "Manager Agent", dark)
    _draw_box(ax, cx, 6.8, 5.2, 0.75, "Department Classification\n(structured RoutingDecision)",
              mid, fontsize=10)

    for y1, y2 in [(11.6, 11.1), (10.3, 9.8), (9.0, 8.5), (7.7, 7.25)]:
        _draw_arrow(ax, cx, y1, cx, y2)

    # Clarification path back to the user (dashed, left side)
    _draw_box(ax, 2.2, 8.1, 3.4, 0.9, "Clarification\nQuestion", "#C0703A", fontsize=10)
    _draw_arrow(ax, cx - 2.6, 6.8, 2.2, 7.63, color="#C0703A", dashed=True,
                connection="arc3,rad=-0.25")
    _draw_arrow(ax, 2.2, 8.55, cx - 1.75, 11.9, color="#C0703A", dashed=True,
                connection="arc3,rad=0.35")
    ax.text(2.0, 6.7, "ambiguous /\nlow confidence", fontsize=9,
            color="#C0703A", ha="center", style="italic")

    # Five department branches
    dept_labels = {
        "IT": "IT Agent", "Finance": "Finance Agent", "HR": "HR Agent",
        "Admin": "Admin Agent", "Compliance": "Compliance Agent",
    }
    xs = [1.9, 4.45, 7.0, 9.55, 12.1]
    for x, dept in zip(xs, DEPARTMENTS):
        _draw_box(ax, x, 5.0, 2.3, 0.8, dept_labels[dept], dept_color, fontsize=10)
        _draw_arrow(ax, cx, 6.4, x, 5.45)
        _draw_arrow(ax, x, 4.6, cx, 3.75)

    _draw_box(ax, cx, 3.3, 3.8, 0.75, "Final Response", dark)
    _draw_box(ax, cx, 2.0, 4.6, 0.75, "Conversation History\n(session state)", mid, fontsize=10)
    _draw_arrow(ax, cx, 2.92, cx, 2.42)

    # Legend
    legend_items = [
        (dark, "Core pipeline"),
        (dept_color, "Department agents (one selected per query)"),
        ("#C0703A", "Clarification path"),
    ]
    for i, (color, label) in enumerate(legend_items):
        y = 0.9 - 0.0 * i
        x = 1.0 + i * 4.6
        ax.add_patch(mpatches.Rectangle((x, y - 0.12), 0.45, 0.3,
                                        facecolor=color, edgecolor="#1F4E79"))
        ax.text(x + 0.6, y, label, fontsize=9, va="center", color="#333333")

    ax.set_facecolor(light)
    fig.patch.set_facecolor("white")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info("Workflow chart written to %s", output_path)
    return output_path


# --------------------------------------------------------------------------
# Workflow chart (Mermaid source)
# --------------------------------------------------------------------------

MERMAID_SOURCE = """\
---
title: Vikram AI Tech - Multi-Agent Customer Support Workflow
---
flowchart TD
    USER([User]) --> UI[Streamlit Chat UI]
    UI --> VALIDATE[Input Validation]
    VALIDATE --> MANAGER[Manager Agent]
    MANAGER --> DECISION{Department Classification<br/>structured RoutingDecision}

    DECISION -- "ambiguous / low confidence" --> CLARIFY[Clarification Question]
    CLARIFY -.-> USER

    DECISION --> IT[IT Agent]
    DECISION --> FINANCE[Finance Agent]
    DECISION --> HR[HR Agent]
    DECISION --> ADMIN[Admin Agent]
    DECISION --> COMPLIANCE[Compliance Agent]

    IT --> RESPONSE[Final Response]
    FINANCE --> RESPONSE
    HR --> RESPONSE
    ADMIN --> RESPONSE
    COMPLIANCE --> RESPONSE

    RESPONSE --> HISTORY[(Conversation History<br/>session state)]
    HISTORY --> UI

    classDef core fill:#1F4E79,color:#fff,stroke:#1F4E79
    classDef dept fill:#3E8E7E,color:#fff,stroke:#1F4E79
    classDef warn fill:#C0703A,color:#fff,stroke:#8a4f27

    class USER,MANAGER,RESPONSE core
    class IT,FINANCE,HR,ADMIN,COMPLIANCE dept
    class CLARIFY warn
"""


def generate_workflow_chart_mmd(output_path: Path) -> Path:
    """Write the editable Mermaid version of the workflow chart."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(MERMAID_SOURCE, encoding="utf-8")
    logger.info("Mermaid workflow written to %s", output_path)
    return output_path


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def generate_all_documents(data_dir: Path = DATA_DIR) -> dict[str, Path]:
    """Generate every project document; returns the created file paths."""
    try:
        return {
            "pdf": generate_development_plan_pdf(data_dir / "development_plan.pdf"),
            "png": generate_workflow_chart_png(data_dir / "workflow_chart.png"),
            "mmd": generate_workflow_chart_mmd(data_dir / "workflow_chart.mmd"),
        }
    except DocumentGenerationError:
        raise
    except Exception as exc:
        logger.exception("Document generation failed: %s", exc.__class__.__name__)
        raise DocumentGenerationError(
            f"Document generation failed: {exc.__class__.__name__}"
        ) from exc


def main() -> int:
    setup_logging("INFO")
    try:
        paths = generate_all_documents()
    except DocumentGenerationError as exc:
        print(f"ERROR: {exc}")
        return 1
    print("Generated project documents:")
    for label, path in paths.items():
        size_kb = path.stat().st_size / 1024
        print(f"  [{label}] {path}  ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
