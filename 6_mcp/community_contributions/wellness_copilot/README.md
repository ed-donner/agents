# Wellness Copilot

Local-first **wellness journaling** demo: Gradio UI, SQLite mood/journal storage, and an OpenAI Agents runner that composes several MCP servers (custom wellness tools, LibSQL memory, sandbox filesystem, `mcp-server-fetch` for a librarian sub-agent).

**This is not medical advice, crisis support, or therapy.** See `content/crisis_resources.md`.

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) to run MCP subprocesses the same way as the course labs
- Node.js with `npx` (for `mcp-memory-libsql` and `@modelcontextprotocol/server-filesystem`)
- `OPENAI_API_KEY` in `.env` (copy from `.env.example`)

On **Windows**, MCP stdio servers are often run via **WSL** in this course; see `setup/SETUP-WSL.md` in the repo root if local MCP fails.

## Run

From this directory:

```bash
cp .env.example .env
# edit .env — add OPENAI_API_KEY

uv sync
uv run wellness_app.py
```

Open the local URL Gradio prints (usually `http://127.0.0.1:7860`).

## What to try

1. **Mood & journal** — log entries (stored in `wellness.db`).
2. **Care plan** — edit markdown; saved as `content/care_plan_{user_id}.md`, also available to the agent via MCP resource `wellness://care_plan/{user_id}`.
3. **Coach** — asks the agent to use tools. The librarian sub-agent uses **fetch** with prompts restricted to allowlisted hosts; the wellness server also exposes `fetch_psychoeducation_page` with a hard host check (`allowlist.py`).

Optional: set `PUSHOVER_USER` and `PUSHOVER_TOKEN` so the coach can call `send_gentle_reminder`.

## Layout

| File | Role |
|------|------|
| `wellness_server.py` | FastMCP: mood, journal, grounding, allowlisted HTTP fetch, export, Pushover, resources |
| `wellness_mcp_params.py` | Stdio params for coach + librarian |
| `wellness_coach.py` | `AsyncExitStack` + librarian `as_tool()` |
| `wellness_app.py` | Gradio UI |
| `wellness_store.py` | SQLite |
| `content/` | Crisis copy + default care plan |
