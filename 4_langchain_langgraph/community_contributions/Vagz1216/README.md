# Deep Research Agent — LangGraph

Agentic research pipeline using **LangGraph** and open-source models.

## Pipeline

```
Clarify → Plan → Search (parallel) → Sufficiency check → Write → Evaluate → Email
```

1. **Clarifier** — generates 3 scoping questions; user picks one and adds context
2. **Planner** — turns query + clarification into 5-8 prioritised search terms
3. **Searcher** — runs all queries in parallel via DuckDuckGo (no API key needed)
4. **Sufficiency checker** — approves evidence or triggers up to 2 extra search rounds
5. **Writer** — produces a Markdown report (1000+ words), streamed live
6. **Evaluator** — scores 0-10; approves or requests one revision
7. **Emailer** — sends the approved report via SendGrid

## Setup

```bash
uv pip install -r requirements.txt
cp .env.example .env   # fill in your keys
```

Required env vars:

| Variable | Required | Notes |
|---|---|---|
| `GROQ_API_KEY` | If using Groq | Default provider |
| `CEREBRAS_API_KEY` | If using Cerebras | |
| `OPENROUTER_API_KEY` | If using OpenRouter | |
| `OPENAI_API_KEY` | If using OpenAI | |
| `SENDGRID_API_KEY` | Yes | For email delivery |
| `SENDGRID_FROM_EMAIL` | Yes | Verified sender |
| `SENDGRID_TO_EMAIL` | Yes | Recipient |
| `LANGCHAIN_API_KEY` | Optional | LangSmith tracing |
| `RESEARCH_PROVIDER` | Optional | `groq` (default) |

## Run

```bash
python app.py          # standalone Gradio app
# or open deep_research_langgraph.ipynb in Jupyter
```

## File structure

| File | Purpose |
|---|---|
| `models.py` | Pydantic schemas and `ResearchState` TypedDict |
| `tools.py` | `web_search` (DuckDuckGo) and `send_report_email` (SendGrid) |
| `agent.py` | LLM setup, guardrails, node functions, routing, graphs |
| `app.py` | Gradio UI — two-phase flow with streaming and session management |
| `deep_research_langgraph.ipynb` | Notebook entrypoint |
| `requirements.txt` | Python dependencies |
