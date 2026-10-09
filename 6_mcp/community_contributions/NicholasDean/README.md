# Nicholas Dean - Week 6 (MCP)

A mini trading floor - the capstone architecture: multiple trader agents over multiple MCP servers.

```
accounts_server.py   # FastMCP: get_balance, buy_shares + accounts://report (knows nothing about prices)
market_server.py     # FastMCP: get_price + market://prices (fixed table; course uses live data)
trading_floor.py     # runs trader agents concurrently; each stacks BOTH servers via AsyncExitStack
```

Each trader is an OpenAI Agents-SDK agent: it stacks the accounts + market MCP servers, looks up
prices from the market, and records trades through its own account. The floor runs the traders
concurrently with `asyncio.gather`. The full course version adds a push server and a Gradio
dashboard on a timer; this keeps the architecture with no paid market feed.

Run: `uv run python trading_floor.py` (needs `OPENAI_API_KEY`).
