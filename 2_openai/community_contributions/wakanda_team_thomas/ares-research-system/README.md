# ARES: Autonomous Research & Extraction System

ARES is a multi-agent deep research engine built on the **OpenAI Agents SDK**. It uses a hierarchical orchestration pattern to plan, execute, and synthesize web research into structured Markdown reports — with optional email delivery via Resend.

## Key Features

- **Hierarchical Orchestration**: A Lead Architect (Manager) coordinates specialist agents as tools.
- **Live Web Search**: Tavily API integration for real-time, AI-optimized web research with recency prioritization.
- **Structured Reports**: Pydantic-enforced output with executive summary, sections, and cited sources.
- **Email Delivery**: Styled HTML email reports via Resend with Human-in-the-Loop approval.
- **Safety Guardrails**: Input guardrail powered by a safety classifier agent that blocks harmful queries.
- **Streaming Progress**: Real-time activity log in the Gradio UI via `Runner.run_streamed()`.
- **Gradio UI**: Interactive web interface deployable on Hugging Face Spaces.
- **CLI Mode**: Run research directly from the terminal with `--query`.

## Architecture

ARES follows the **Manager-Specialist** design pattern:

```
User Query
    │
    ▼
┌─────────────────────┐
│  Safety Guardrail   │ ── blocks harmful queries
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Research Architect  │ ── plans research, coordinates agents
│  (gpt-4o)           │
└─────────┬───────────┘
          ├──────────────────────┐
          ▼                      ▼
┌──────────────────┐   ┌──────────────────┐
│  Web Specialist  │   │  Report Editor   │
│  (gpt-4o-mini)   │   │  (gpt-4o-mini)   │
│  + Tavily Search │   │  → ResearchReport│
└──────────────────┘   └──────────────────┘
                                 │
                                 ▼
                       ┌──────────────────┐
                       │ Notification Agent│ ── HITL email delivery
                       │ (gpt-4o-mini)    │
                       │ + Resend API     │
                       └──────────────────┘
```

### Agents

| Agent | Role | Model | Tools |
|-------|------|-------|-------|
| **Research Architect** | Plans research, delegates to specialists | gpt-4o | Web Specialist, Report Editor |
| **Web Specialist** | Searches the web, extracts findings | gpt-4o-mini | `travily_web_search` |
| **Report Editor** | Compiles findings into structured report | gpt-4o-mini | — (structured output) |
| **Notification Agent** | Sends report via email | gpt-4o-mini | `send_email` |
| **Safety Classifier** | Validates queries before processing | gpt-4o-mini | — (input guardrail) |

### Schemas (Pydantic)

| Model | Purpose |
|-------|---------|
| `ResearchTask` | A single research sub-task (title, query, goal) |
| `ResearchPlan` | The Architect's strategy (query, summary, tasks) |
| `ResearchFinding` | A fact from the Web Specialist (content, source, quality) |
| `ReportSection` | A chapter of the report (heading, content) |
| `ResearchReport` | The final output (title, subject line, summary, sections, sources) |

## Setup

This project uses **uv** for dependency management.

### 1. Installation

```bash
git clone https://github.com/youruser/ares-research
cd ares-research

# Sync dependencies
uv sync
```

### 2. Configuration

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=sk-proj-xxxx
TAVILY_API_KEY=tvly-xxxx       # For Tavily web search (free: 1000 queries/month)
RESEND_API_KEY=re_xxxx         # For Resend email delivery (free: 3000 emails/month)
```

## Usage

### CLI Mode

```bash
# Research with email delivery (prompts for approval)
uv run main.py --query "Analyze the 2026 solid-state battery breakthroughs"

# Research without email
uv run main.py --query "Latest trends in AI" --no-email

# Research with custom recipient
uv run main.py --query "Latest trends in AI" --email someone@example.com
```

### Gradio UI (Local)

```bash
uv run app.py
```

Then open [http://localhost:7860](http://localhost:7860). The UI features:
- Real-time streaming progress with activity log
- Report rendered in Markdown
- Email section appears after report is generated (Human-in-the-Loop)

### Hugging Face Spaces (Production)

1. Create a new Space on Hugging Face with the **Gradio** SDK.
2. Add your API keys as **Secrets** in the Space settings:
   - `OPENAI_API_KEY`
   - `TAVILY_API_KEY`
   - `RESEND_API_KEY`
3. Push the repository to the Space:

```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ares-research
git push hf main
```

## Project Structure

```
ares-research-system/
├── ares_agents/              # Agent definitions
│   ├── architect.py          # Research Architect (manager)
│   ├── web_specialist.py     # Web Specialist (Tavily search)
│   ├── report_editor.py      # Report Editor (structured output)
│   ├── notificator.py        # Notification Agent (Resend email)
│   └── guardrails.py         # Input safety guardrail
├── ares_tools/               # Function tools
│   ├── search.py             # travily_web_search tool
│   └── email.py              # send_email tool (styled HTML template)
├── ares_schema/              # Pydantic models
│   └── models.py             # ResearchPlan, ResearchFinding, ResearchReport, etc.
├── ares_data/                # Runtime data (SQLite, gitignored)
├── main.py                   # CLI entry point
├── app.py                    # Gradio web UI
├── pyproject.toml            # Project config & dependencies
├── requirements.txt          # Pinned dependencies
└── .env                      # API keys (gitignored)
```

## Safety & Governance

- **Input Guardrail**: All queries are vetted by a safety classifier agent before the Architect processes them. Harmful, illegal, or abusive queries are blocked.
- **Human-in-the-Loop Email**: Reports are shown to the user for review before email delivery. In CLI mode, the user must confirm with `Y/n`. In the UI, a "Send Email" button appears only after the report is ready.
- **Traceability**: The OpenAI Agents SDK provides full trace logging for every run.

## License

Apache-2.0
