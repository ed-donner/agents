# Sidekick

Gradio session state, LangGraph worker / tools / evaluator loop, optional per-session context field, and extra sandbox-focused tools (`fetch_url_text`, `append_worklog`, `pretty_json`, `list_sandbox_files`).

## Run

From this directory (repo `.env` or local env is fine):

```bash
uv run python app.py
```

## Environment

- `OPENAI_API_KEY` — required for the models.
- `SERPER_API_KEY` — enables the `search` tool (otherwise the tool returns a short notice).
- `PUSHOVER_TOKEN` / `PUSHOVER_USER` — optional; without them push returns a clear skip message.
- `SIDEKICK_HEADLESS` — set to `1` or `true` to run Chromium headless (useful on servers).

Artifacts land under `sandbox/` (gitignored except `.gitkeep`).
