# Setup — US Equities + Crypto contribution

This folder is a **Week 6 community contribution**. Clone the **repo** (not this folder alone). MCP Python servers and account wiring for this variant live **in this directory**; `database.py`, `tracers.py`, and `util.py` still come from `6_mcp/` on `sys.path`.

## Prerequisites

- Python 3.12+ and `uv` (as in the course)
- From repo root: `uv sync`

## Environment

Copy `.env.example` to `.env` at repo root if needed, then set at least:

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Recommended LLM provider for traders |
| `OPENROUTER_API_KEY` | Optional fallback |
| `CEREBRAS_API_KEY` | Optional fallback |
| `POLYGON_API_KEY` | US equity prices (optional; fallback exists) |
| `RUN_EVERY_N_MINUTES` | Scheduler interval (e.g. `1` for demos) |
| `RUN_EVEN_WHEN_MARKET_IS_CLOSED` | `true` to run outside US hours |

## Reset accounts (same as instructor flow, multi-asset strategies)

From directory `6_mcp`:

```bash
uv run community_contributions/Vagz1216_us_equities_crypto/reset.py
```

This resets **Warren, George, Ray, Cathie** to starting cash and applies strategies that mention **US equities + crypto**.

You can also use the class-wide reset (same DB), now aligned with multi-asset in `6_mcp/reset.py`:

```bash
uv run reset.py
```

## Run trading floor

From this directory:

```bash
uv run trading_floor.py
```

Or from `6_mcp`:

```bash
uv run community_contributions/Vagz1216_us_equities_crypto/trading_floor.py
```

## Run UI

```bash
uv run app.py
```

(from this directory, or use the full path under `6_mcp` as above)

## Files in this contribution

| File | Role |
|------|------|
| `market.py` / `market_server.py` | Multi-asset pricing + MCP market tool |
| `mcp_params.py` | MCP server wiring (all stdio Python servers in this folder) |
| `accounts*.py`, `push_server.py`, `ddg_search_server.py` | Account + push + search MCP (local copies) |
| `memory/` | Per-trader LibSQL files for researcher MCP |
| `templates.py` | Trader/research prompts (equities + crypto) |
| `traders.py` | Agent loop + model fallback |
| `trading_floor.py` | Scheduler |
| `app.py` | Gradio UI (asset split + tables) |
| `reset.py` | Reset accounts + multi-asset strategies |

From `6_mcp/` only: `database.py`, `tracers.py`, `util.py`.
