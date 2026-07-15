# Vikram AI Tech — Multi-Agent Customer Support Chatbot

An internal first-level customer-support assistant for **Vikram AI Tech**,
built with **Microsoft AutoGen AgentChat**, **Streamlit**, and **OpenAI
`gpt-4.1-mini`**. A manager agent classifies every employee question with a
validated structured routing decision, then exactly one of five department
specialists (IT, Finance, HR, Administration, Compliance) answers it.

---

## 1. Project Overview

Employees ask support questions in a chat interface. Behind the scenes:

1. The **Manager Agent** analyses the question (with recent conversation
   context) and returns a structured `RoutingDecision` (department,
   confidence, brief reason, clarification flag, optional secondary
   department) validated with Pydantic.
2. If the question is ambiguous or the confidence is below **0.65**, the app
   asks **one clarification question** instead of guessing.
3. Otherwise the original question is sent to **exactly one** department
   agent, whose answer is shown together with the selected department and the
   routing confidence.

## 2. Business Use Case

Vikram AI Tech receives internal support requests across five departments.
Manually triaging them is slow and error-prone. This assistant provides
instant, correctly routed first-level guidance, deflects routine questions,
and tells employees exactly which human team to contact when a real action
(password reset, approval, booking) is required — it never pretends to have
performed such actions itself.

## 3. Key Features

- 🧭 **Structured routing** — Pydantic-validated manager output, no fragile
  keyword matching.
- 🎯 **Confidence threshold** — low-confidence routes become clarification
  requests.
- 🏢 **Five department specialists** — each with focused responsibilities,
  explicit limitations, and security rules.
- 🔁 **Cross-functional detection** — an optional secondary department is
  surfaced in the UI.
- 💬 **Full chat experience** — history in session state, starter questions,
  clear-conversation button, department & confidence badges.
- 🔐 **Security-first** — prompt-injection resistance, fixed agent mapping,
  no secrets in code/logs/UI, safe error messages.
- 📄 **Generated project documents** — development-plan PDF and workflow
  charts (PNG + Mermaid) produced by one script.
- ✅ **Offline test suite** — 50+ tests, zero real API calls.

## 4. Multi-Agent Architecture

```text
User
  ↓
Streamlit Chat UI  (app.py)
  ↓
Chat Service       (src/services/chat_service.py)
  ↓
Manager Agent      (structured RoutingDecision)
  ├── ambiguous / low confidence → Clarification question → User
  ↓
Selected Department Agent  (exactly one)
  ↓
Final Response  (department + confidence + answer)
  ↓
Conversation History  (st.session_state.messages)
```

All six agents are AutoGen `AssistantAgent` instances built by a **central
factory** (`src/agents/agent_factory.py`) sharing one
`OpenAIChatCompletionClient`. Orchestration is a controlled two-step
pipeline — there is no free-form multi-agent conversation.

## 5. Department-Agent Responsibilities

| Agent | Handles | Key limits |
|---|---|---|
| `manager_agent` | Classification only — returns a structured routing decision | Never answers questions; ignores user routing demands |
| `it_support_agent` | Accounts, passwords, email, devices, software, VPN, network, printers, app errors | Guidance only; never requests/exposes secrets |
| `finance_support_agent` | Invoices, payments, reimbursements, expenses, budgets, payroll process, vendors, POs | No investment/tax/legal advice; cannot approve or pay |
| `hr_support_agent` | Leave, attendance, benefits, recruitment, on/offboarding, reviews, policies, training | Careful with personal data; cannot approve leave |
| `admin_support_agent` | Facilities, meeting rooms, visitors, supplies, travel, maintenance, ID cards, cafeteria | Explains request processes; cannot book/reserve |
| `compliance_support_agent` | Policies, privacy, audits, ethics, conflicts of interest, retention, reporting | Not legal advice; escalates serious concerns |

## 6. Routing Workflow

The manager returns this structured result for every question:

```python
class RoutingDecision(BaseModel):
    department: Literal["IT", "Finance", "HR", "Admin", "Compliance", "Clarification"]
    confidence: float          # 0.0 – 1.0
    brief_reason: str          # one short sentence
    needs_clarification: bool
    clarification_question: str | None
    secondary_department: Literal["IT", "Finance", "HR", "Admin", "Compliance"] | None
```

Routing rules: clear single-department queries go straight to that
department; cross-functional queries get a primary + secondary department;
ambiguous or sub-threshold (< 0.65) queries produce one concise
clarification question; invalid manager output degrades safely to a
clarification request (deterministic error recovery only — never keyword
routing).

## 7. Technology Stack

| Layer | Technology |
|---|---|
| Agents | Microsoft AutoGen (`autogen-agentchat`, `autogen-ext[openai]`) |
| LLM | OpenAI `gpt-4.1-mini` (configurable via `OPENAI_MODEL`) |
| UI | Streamlit |
| Validation | Pydantic v2 structured outputs |
| Documents | ReportLab (PDF), Matplotlib (PNG chart), Mermaid (.mmd) |
| Config | python-dotenv + validated `AppConfig` |
| Tests | Pytest + pytest-asyncio (fully offline) |

## 8. Prerequisites

- **Python 3.10 or later** (developed and verified on 3.12)
- An **OpenAI API account** with access to `gpt-4.1-mini`
  (create a key at <https://platform.openai.com/api-keys>)
- ~500 MB disk space for the virtual environment

## 9. Installation

Clone / open the project folder, then create a virtual environment.

**All platforms:**

```bash
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

## 10. Configure the `.env` File

**Windows (PowerShell / CMD):**

```powershell
copy .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Then open `.env` and set your real key:

```env
OPENAI_API_KEY=sk-your-real-key-here
OPENAI_MODEL=gpt-4.1-mini
LOG_LEVEL=INFO
```

> 🔑 **Getting a key:** sign in at <https://platform.openai.com>, open
> *API keys*, create a new secret key, and paste it into `.env`. The `.env`
> file is git-ignored and must never be committed. The default (and
> documented) model is `gpt-4.1-mini`; `OPENAI_MODEL` may override it.
> Optional: `ROUTING_CONFIDENCE_THRESHOLD` (default `0.65`).

## 11. Run the Application

```bash
streamlit run app.py
```

Streamlit opens the app at `http://localhost:8501`.

## 12. Regenerate the PDF and Workflow Charts

```bash
python scripts/generate_project_documents.py
```

This rebuilds all three files in `data/`:

- `data/development_plan.pdf` — multi-page development plan
- `data/workflow_chart.png` — rendered routing workflow diagram
- `data/workflow_chart.mmd` — editable Mermaid source of the same diagram

## 13. Run the Tests

```bash
pytest -v
```

The suite is fully offline — agents are replaced with fakes, so **no paid
OpenAI API calls are ever made by tests**.

## 14. Folder Structure

```text
vikram_ai_tech_support/
├── app.py                          # Streamlit entry point
├── README.md
├── requirements.txt
├── pytest.ini
├── .env.example                    # safe placeholders (copy to .env)
├── .gitignore
├── src/
│   ├── config.py                   # validated environment configuration
│   ├── agents/
│   │   ├── agent_factory.py        # model client + all agent construction
│   │   ├── manager_agent.py        # routing manager definition
│   │   ├── it_agent.py             # department agent specs …
│   │   ├── finance_agent.py
│   │   ├── hr_agent.py
│   │   ├── admin_agent.py
│   │   └── compliance_agent.py
│   ├── models/routing_models.py    # RoutingDecision, SupportResponse
│   ├── prompts/system_prompts.py   # all system messages + security rules
│   ├── services/
│   │   ├── chat_service.py         # orchestration (manager → one specialist)
│   │   └── routing_service.py      # threshold + fallback around the manager
│   ├── ui/styles.py                # conservative custom CSS
│   └── utils/
│       ├── async_utils.py          # safe coroutine execution in Streamlit
│       ├── exceptions.py           # typed errors with safe user messages
│       ├── logging_config.py       # centralized logging
│       └── response_utils.py       # output extraction, bounded context
├── scripts/generate_project_documents.py
├── data/                           # generated PDF + workflow charts
└── tests/                          # offline pytest suite
```

## 15. Example User Questions

| Question | Routed to |
|---|---|
| “I cannot connect to the company VPN.” | IT |
| “My expense reimbursement is still pending.” | Finance |
| “How many annual leave days do employees receive?” | HR |
| “The air conditioning is not working in the meeting room.” | Admin |
| “I need to report a possible data privacy violation.” | Compliance |
| “I need help with my request.” | Clarification question |

## 16. Troubleshooting

| Symptom | Fix |
|---|---|
| *“The application is not configured correctly”* on startup | Copy `.env.example` to `.env` and set `OPENAI_API_KEY`; restart. |
| Authentication / 401 errors in logs | The API key is invalid or revoked — create a new key. |
| Rate-limit or timeout messages | Wait and retry; check your OpenAI usage limits. |
| `ModuleNotFoundError` | Activate the virtual environment and re-run `pip install -r requirements.txt`. |
| App answers “could not determine the right department” | Transient routing failure — rephrase or retry. |
| PowerShell blocks venv activation | Run `Set-ExecutionPolicy -Scope Process RemoteSigned`, then activate again. |

## 17. Security Practices

- API key lives only in the git-ignored `.env`; it is validated at startup
  and never hard-coded, logged, printed, or displayed.
- Every agent has prompt-injection resistance rules (role retention,
  untrusted user content, no prompt/credential disclosure).
- Routing uses business intent, and the department→agent mapping is a fixed
  dictionary — user input can never select an arbitrary agent or object.
- No `eval` / `exec` / shell execution / unsafe deserialization.
- Users see friendly error messages; stack traces stay in logs.
- Logs exclude secrets and full user messages; transcripts are not written
  to disk.
- Agents never claim to have completed real actions and never request
  passwords, OTPs, or tokens.

## 18. Known Limitations

- No real integrations: the assistant gives guidance but cannot reset
  passwords, book rooms, or approve anything.
- Company policies are not loaded from real documents; agents explicitly say
  when policy details are unavailable.
- Conversation history lives only in the browser session (lost on refresh).
- No authentication layer in v1 — intended to run behind internal SSO.
- Routing quality depends on the LLM; the clarification loop mitigates but
  cannot eliminate misroutes.

## 19. Future Enhancements

- Real tool integrations (ticketing, room booking, leave balances).
- Retrieval (RAG) over the actual company policy library.
- SSO login and persistent per-user conversations.
- Feedback buttons and routing-quality analytics.
- Multi-language support and human-handoff escalation.

## 20. Contributing

1. Create a feature branch.
2. Keep the architecture: prompts in `src/prompts`, agent construction in
   the factory, orchestration in services, UI in `app.py`.
3. Add or update tests (they must stay offline) and run `pytest -v`.
4. Never commit `.env` or any secret.

## 21. License / Internal-Use Notice

Internal Vikram AI Tech project for demonstration and internal support use.
Not licensed for external redistribution.
