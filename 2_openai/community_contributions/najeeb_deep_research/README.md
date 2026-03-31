# Deep Research (Gradio + OpenAI Agents)

A multi-agent “deep research” demo: you enter a topic, answer three clarifying questions in the UI, then the app plans web searches, gathers summaries, writes a long markdown report, and emails it via SendGrid.

## What it does

1. **Gradio UI** (`deep_research.py`) — Two steps: submit a research query, then answer three fixed clarifying questions. Answers and the query are stored in an in-memory `session_state` (see `state.py`).
2. **Planner** (`planner_agent.py`) — Produces a structured list of **five** search items (`WebSearchPlan`). It calls the `clarifying_questions` tool once so the model receives the same answers the user typed (bridging the UI and the agent loop).
3. **Search** (`search_agent.py` + `web_search_tool.py`) — For each planned item, an agent uses **Serper** (Google results API) and returns a short summary for downstream synthesis.
4. **Writer** (`writer_agent.py`) — Builds a detailed markdown report (plus a short summary and follow-up ideas) as structured `ReportData`.
5. **Email** (`email_agent.py`) — Converts the report to HTML and sends it with SendGrid.

Orchestration, tracing, and concurrency live in `research_manager.py` (parallel searches with `asyncio`, `Runner.run` with a raised `max_turns` limit for tool-heavy runs).

## LLM and API routing

`deep_research.py` configures the OpenAI-compatible client for **OpenRouter** (`https://openrouter.ai/api/v1`) and `set_default_openai_api("chat_completions")`. Set `OPENAI_API_KEY` to your OpenRouter key (or adjust the base URL for another provider).

Agent definitions still reference `gpt-4o-mini`; OpenRouter maps that to an equivalent model per your account settings.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenRouter API key (used as `AsyncOpenAI` key) |
| `SERPER_API_KEY` | [Serper.dev](https://serper.dev) key for `serper_web_search` |
| `SENDGRID_API_KEY` | SendGrid API key for outbound email |

Optional: load them from a `.env` file in the working directory (`python-dotenv` is used in `deep_research.py` and `web_search_tool.py`).

## Email sender and recipient

`email_agent.py` hardcodes SendGrid `Email` / `To` addresses. Change those to your verified sender and recipient before production use.

## How to run

From this directory (so imports and `.env` resolve as expected), with a virtualenv that has the project dependencies installed (e.g. `openai-agents`, `gradio`, `openai`, `python-dotenv`, `httpx`, `sendgrid`, `pydantic`):

```bash
python deep_research.py
```

The app opens in your browser (`gradio`).

## Project layout

| File | Role |
|------|------|
| `deep_research.py` | Gradio UI, OpenRouter client setup |
| `research_manager.py` | End-to-end pipeline: plan → search → write → email |
| `planner_agent.py` | `WebSearchPlan` / `WebSearchItem` schemas and planner agent |
| `search_agent.py` | Web search + summarization agent |
| `web_search_tool.py` | `serper_web_search` tool (HTTP POST to Serper) |
| `writer_agent.py` | Report generation (`ReportData`) |
| `email_agent.py` | HTML email via SendGrid |
| `clarifying_questions_tool.py` | Tool that returns answers from `session_state` |
| `state.py` | Shared `session_state` dict for the Gradio session |

## Notes

- **Clarifying flow**: The UI collects answers *before* research starts; the planner’s tool call is how those answers enter the agent turn without duplicating Gradio logic inside the SDK.
- **Search count**: `HOW_MANY_SEARCHES` in `planner_agent.py` is set to **5**; change it there if you want more or fewer queries per run.
