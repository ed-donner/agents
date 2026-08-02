# Week 4 — LangGraph mini sidekick (assignment)

Community submission for **Week 4** (`4_langgraph`): a **Sidekick-style** LangGraph app aligned with **`4_lab4.ipynb`** / `sidekick.py`, without Playwright.

## What it covers

| Course concept | Implementation |
|----------------|----------------|
| `StateGraph` + `TypedDict` state | `messages` + success criteria + evaluator fields |
| Structured evaluator output | `EvaluatorOutput` (Pydantic) |
| Worker → tools → worker | `ToolNode` with Wikipedia + Python REPL |
| Evaluator loop | Retry worker until criteria met or user input needed |
| Checkpointing | `MemorySaver` + `thread_id` |

## Run

From the **repository root** (`agents/`), with dependencies from the main `pyproject.toml`:

```bash
cd /Users/mac/Documents/agents
uv run python 4_langgraph/community_contributions/idumachika_week4/mini_sidekick.py
```

Set **`OPENAI_API_KEY`** in **`agents/.env`**. Keys starting with **`sk-or-`** use OpenRouter automatically; otherwise optional **`OPENAI_BASE_URL`**.

## Safety

**PythonREPLTool** executes code locally—only use with inputs you trust. The course sandbox pattern is optional; this demo runs from your machine.

## PR

Add this folder under `4_langgraph/community_contributions/` and open a PR to [ed-donner/agents](https://github.com/ed-donner/agents).
