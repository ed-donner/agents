# MCP in three modes

one agent that uses **three MCP deployment patterns**, with **no  MCP dependencies** (only your LLM API key).


| Mode                              | Server                       | What it uses                                                                                  |
| --------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------- |
| **1. Local process, local data**  | `notes_server.py` (stdio)    | SQLite file under `data/notes.db` — no network                                                |
| **2. Local process, remote APIs** | `weather_server.py` (stdio)  | [Open-Meteo](https://open-meteo.com/) — free, **no API key required**                         |
| **3. Remote / hosted transport**  | `remote_sse_server.py` (SSE) | Same machine, **HTTP + SSE** instead of stdio; tools are trivial (time/echo), no external API |


The third case illustrates **remote-style MCP** (network transport). Here the server runs on `127.0.0.1` so you do not need a cloud host; production would point the SSE URL at a deployed service instead.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) and this repo’s root `pyproject.toml` / `uv.lock`
- An LLM API key: set `**OPENAI_API_KEY`** in the repo root `.env`  
  - If you use **OpenRouter**, also set `**OPENAI_BASE_URL=https://openrouter.ai/api/v1`** (otherwise the default OpenAI host will reject a non-OpenAI key).  

No keys are required for Open-Meteo or the SQLite notes DB.

## Run the demo

From the **repository root** (`agents/`, where `uv.lock` lives):

```bash
uv run python 6_mcp/community_contributions/najeeb_mcp/run_demo.py
```

The script starts the SSE server on `**127.0.0.1:8765**` (override with `SERVER_MCP_SSE_PORT` / `SERVER_MCP_SSE_HOST`), connects three MCP clients, and runs one agent turn.

## Run servers individually (optional)

```bash
# Terminal A — remote SSE (for manual experiments with an MCP client)
uv run python 6_mcp/community_contributions/najeeb_mcp/remote_sse_server.py
# Then point an SSE client at http://127.0.0.1:8765/sse

# Stdio servers are normally spawned by `run_demo.py` or your agent; to smoke-test:
uv run python 6_mcp/community_contributions/najeeb_mcp/notes_server.py
```

## Files


| File                   | Role                                                             |
| ---------------------- | ---------------------------------------------------------------- |
| `notes_server.py`      | FastMCP stdio — local SQLite                                     |
| `weather_server.py`    | FastMCP stdio — Open-Meteo HTTP                                  |
| `remote_sse_server.py` | FastMCP **SSE** — `remote_`* tools                               |
| `run_demo.py`          | Subprocess SSE + `MCPServerStdio` ×2 + `MCPServerSse` + `Runner` |
| `data/`                | Local DB directory (`.db` gitignored)                            |


