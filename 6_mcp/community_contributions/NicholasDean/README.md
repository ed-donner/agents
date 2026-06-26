# Nicholas Dean - Week 6 (MCP)

Both sides of the Model Context Protocol - writing a server and consuming it.

- `accounts_server.py` - a tiny FastMCP server exposing a toy trading account: `get_balance`
  and `buy_shares` tools plus an `accounts://report` resource.
- `trader.py` - an OpenAI Agents-SDK agent that spawns the server over stdio and trades; it
  discovers the server's tools automatically.
- `SUMMARY.md` - what I learned this week.

Run: `uv run python trader.py` (needs `OPENAI_API_KEY`).
