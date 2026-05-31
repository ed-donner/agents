# Simple MCP Server + Client (Week 6)

This is a minimal MCP example with:
- A **FastMCP server** that exposes `current_date` and `current_datetime`
- A **client** using the OpenAI Agents SDK (`MCPServerStdio`)

## Setup
Create a `.env` file in this folder. Both OpenAI and OpenRouter are supported.

OpenAI:
```
OPENAI_API_KEY=sk-...
MODEL=gpt-4o-mini
```

OpenRouter:
```
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
MODEL=openai/gpt-4o-mini
```

## Run
From this folder:
```
uv run python client.py
```

You should see a response that includes the current UTC date and time.

## Notes
- The MCP server runs via stdio inside the client process.
- Tools are defined in `server.py` and consumed by the agent in `client.py`.
