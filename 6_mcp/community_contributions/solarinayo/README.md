# Week 6 — Multi-agent multi-exchange paper “auto-trader” (solarinayo)

**MCP Week contribution:** two **stdio MCP servers** plus a **two-agent floor** (OpenAI Agents SDK) that mimics a **smart routing** workflow across *logical* venues (US equity, NSE-style delayed equity, crypto, FX).

This is **paper / simulation only**. It does **not** place real orders. **Not financial advice.**

## What you get

| Component | Role |
|-----------|------|
| `exchange_intel_server.py` | MCP tools: `list_venues`, `get_fx_rate`, `get_crypto_quote`, `get_equity_hint` (optional Polygon), `compare_venues`, `smart_route`. |
| `paper_ledger_server.py` | MCP tools: `get_paper_portfolio`, `propose_paper_order` — append-only JSON journal under `data/paper_state.json`. |
| `run_floor.py` | **VenueScout** agent (intel MCP only) → **AutoTraderClerk** agent (intel + paper MCP) to record aligned paper intents. |

## Prerequisites

- Repo root `.env` with `OPENAI_API_KEY` (same as the rest of the course — never commit `.env`).
- Run from **`agents`** root so `uv run` resolves project deps.
- Optional: `POLYGON_API_KEY` for live US equity *hints* via Polygon in `get_equity_hint`.

## Run (CLI)

```bash
cd /path/to/agents
uv run python 6_mcp/community_contributions/solarinayo/run_floor.py
```

Edit `main()` in `run_floor.py` to change goals, symbols, or risk profile.

## Run (Gradio UI)

```bash
cd /path/to/agents
uv run python 6_mcp/community_contributions/solarinayo/gradio_floor.py
```

Browser opens locally; fill **Goal**, **Symbols**, **Risk profile**, then **Run floor**. Scout and Clerk outputs appear in two panels (same MCP flow as the CLI).

## External APIs

- [Frankfurter](https://www.frankfurter.app/) — FX (ECB series).
- [CoinGecko](https://www.coingecko.com/) — public crypto prices (rate limits; no key).
- Polygon — optional, via `polygon` Python client if key set.

## Security / course tie-in

- Fits **MCP Week**: custom server, tools, resources (`paper://state`), **multiple MCP servers** on one agent.
- **Marketplaces / trust:** only call tools you ship; no arbitrary browsing unless you add fetch MCP yourself.

## License

Same as parent repository; educational use.
