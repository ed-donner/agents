# Week 6 — MCP assessment (idumachika)

Submission for **Week 6 (Model Context Protocol)** aligned with **`6_mcp/2_lab2.ipynb`**.

## What it implements

| Lab / exercise | This folder |
|----------------|-------------|
| **Build your own MCP server** | `date_time_server.py` — FastMCP **stdio** server with `get_today_iso`, `get_datetime_iso`, plus a small **resource** `datetime://now_utc`. |
| **Agent + `MCPServerStdio`** | `date_agent_demo.py` — OpenAI **Agents SDK** agent that uses the server to answer date/time questions. |

Optional “harder” path from the lab (native OpenAI client + your own MCP client) is left as a follow-on; the demo matches the **in-notebook** Agents SDK flow.

## Run the agent demo

From the **repository root** (`agents/`):

```bash
uv run python 6_mcp/community_contributions/idumachika_week6/date_agent_demo.py
```

This starts the MCP server as a subprocess via `uv run` with `cwd` set to **`6_mcp/`** so dependencies resolve like the course `accounts_server` example.

## Run the server alone (debugging)

```bash
cd 6_mcp
uv run community_contributions/idumachika_week6/date_time_server.py
```

## Environment

- **`OPENAI_API_KEY`** in **`agents/.env`**
- For **OpenRouter**, use your usual key; if the Agents SDK does not pick up a custom base URL, set provider env vars per the course OpenRouter notes or use an OpenAI-native key for this demo.

## PR

Add under `6_mcp/community_contributions/` and open a PR to [ed-donner/agents](https://github.com/ed-donner/agents).
