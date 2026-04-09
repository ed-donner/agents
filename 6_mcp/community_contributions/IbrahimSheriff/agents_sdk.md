# OpenAI Agents SDK

- **`Agent`**: instructions, model name, and optional `mcp_servers` or `tools`.
- **`Runner.run`**: runs the agent on a user message; the runtime handles tool loops.
- **`trace`**: context manager for observability (e.g. on platform.openai.com/traces).

For Week 6, wiring **your own** MCP server means: implement tools in Python, run with `uv run your_server.py`, pass the same params dict as in the labs.

## Tip

Keep `*.md` study notes in the same folder as `study_server.py` (`6_mcp/IbrahimSheriff`). For OpenRouter, set `OPENROUTER_API_KEY` and use `https://openrouter.ai/api/v1`.
