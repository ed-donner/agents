# Chrys sidekick (LangGraph + Gradio)

Clarifying questions → structured plan → tool-using worker ↔ evaluator, with **SQLite** checkpoints (`sidekick_checkpoints.sqlite` by default).

## Run

From the repo root (with `uv` / your venv):

```bash
cd 4_langgraph/community_contributions/chrys
uv run python app.py
```

## Environment

| Variable | Purpose |
|----------|---------|
| `OPENROUTER_API_KEY` | Required for `ChatOpenAI` (default model `gpt-4o-mini`, override with `OPENAI_MODEL`) |
| `SERPER_API_KEY` | Optional; enables the `search` tool |
| `SIDEKICK_CHECKPOINT_DB` | Optional path for the SQLite checkpoint file |
| `SIDEKICK_MAX_EVAL_LOOPS` | Max worker↔evaluator cycles (default `8`) |
| `SIDEKICK_RECURSION_LIMIT` | LangGraph max steps per `ainvoke` (default `100`; LangGraph’s default `25` is often too low for tool loops) |
| `PLAYWRIGHT_HEADLESS` | `true` / `false` (default `true`) |

## UI

- **Thread ID** — Shown for the active checkpoint thread; copy it to resume later.
- **Resume thread ID** — Paste a UUID and click **Apply thread ID** to load state from the same DB.
- **Save chat to Markdown** — Writes `exports/sidekick_chat_<timestamp>.md`.
- **Skip clarification** — Jumps straight to plan + worker.
- **Tool trace** — Lists tool names invoked during the last user turn.

## Graph visualization (dev)

```bash
cd 4_langgraph/community_contributions/chrys
uv run python dev_graph.py
```
