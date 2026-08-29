# MCP basics

**Model Context Protocol** connects assistants to tools, resources, and prompts in a standard way.

- **stdio transport**: the client spawns the server process; tools are invoked over JSON-RPC on stdin/stdout.
- **FastMCP** (Python) lets you expose functions as tools with `@mcp.tool()` and docstrings the model reads.
- **MCPServerStdio** in OpenAI Agents SDK wraps a server command (e.g. `uv run study_server.py`) so an `Agent` can call those tools during `Runner.run`.

## Study checklist

1. List available tools after starting the server.
2. Give the agent a goal that requires listing notes, then reading one.
3. Check OpenAI traces to see tool calls.
