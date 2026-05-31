---
title: Deep_Research_with_MCP
app_file: app.py
sdk: gradio
sdk_version: 5.49.1
---
# Deep Research with MCP

This app recreates the deep-research workflow from `2_openai/community_contributions/mayowa`, but rewires the implementation around MCP servers.

## What changed

- Web research uses the Brave Search MCP server instead of `googleserper`.
- Page inspection can use `mcp-server-fetch` when search snippets are not enough.
- Completion alerts are sent through a local `push_server.py` MCP server.
- Email delivery has been removed.

## Environment

Set these variables before running:

- `OPENAI_API_KEY`
- `BRAVE_API_KEY`
- `PUSHOVER_USER` and `PUSHOVER_TOKEN` if you want real push notifications

## Run

```bash
cd 6_mcp/community_contributions/mayowa
uv sync
uv run python app.py
```

## Files

- `app.py`: Gradio UI and clarification flow
- `clarifier.py`: clarification agent plus input guardrail
- `planner.py`: search-plan generation
- `research_agents.py`: search, writer, and notification agents
- `research_manager.py`: MCP orchestration and report streaming
- `mcp_params.py`: MCP server definitions
- `push_server.py`: local MCP push notification server
