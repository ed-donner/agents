# Week 6 MCP PR Draft — US Equities + Crypto Trading Floor

This community contribution extends the original Week 6 class simulation to support a second asset class: crypto (alongside US equities).

## Scope

| Item | Status |
|---|---|
| Keep class architecture (OpenAI Agents SDK + MCP) | ✅ |
| Preserve equities flow | ✅ |
| Add crypto pricing/trading path | ✅ |
| Keep same account buy/sell tools | ✅ |
| Update trader/research prompts for multi-asset decisions | ✅ |
| Surface both asset classes in UI | ✅ |

## What is included

- `market.py` — multi-asset market layer
  - Equities: Polygon (or fallback)
  - Crypto: CoinGecko simple price (BTC/ETH/SOL/BNB/XRP/ADA/DOGE)
- `market_server.py` — MCP market tool using multi-asset prices
- `mcp_params.py` — wires class MCP servers + this contribution’s market server
- `templates.py` — prompts updated for equities + crypto
- `traders.py` — trader orchestration for this contribution
- `trading_floor.py` — scheduler for this contribution
- `app.py` — UI variant with:
  - Total portfolio chart
  - Asset split chart (Equities vs Crypto)
  - Holdings/transactions with `AssetClass` column
- `reset.py` — reset all four traders (same `accounts.db` as the class) with **multi-asset** strategy text
- `SETUP.md` — clone → install → env → reset → run (for reviewers)

**Bundled in this folder** (reliable `uv run` from the contribution path): `accounts.py`, `accounts_server.py`, `accounts_client.py`, `push_server.py`, `ddg_search_server.py`, `mcp_params.py`, and `memory/` for researcher LibSQL.

**Still loaded from `6_mcp/`** via `sys.path`: `database.py`, `tracers.py`, `util.py`.

## After cloning this PR

1. Repo root: `uv sync`
2. Configure `.env` (see `SETUP.md`)
3. From `6_mcp`, reset traders (multi-asset strategies):

```bash
uv run community_contributions/Vagz1216_us_equities_crypto/reset.py
```

Or use the class entrypoint (same DB, same strategies as `6_mcp/reset.py` now):

```bash
uv run reset.py
```

## Run

From repo root or from this folder:

```bash
cd 6_mcp/community_contributions/Vagz1216_us_equities_crypto
export RUN_EVEN_WHEN_MARKET_IS_CLOSED=true
uv run trading_floor.py
```

Optional UI (another terminal, same directory):

```bash
uv run app.py
```

Or from `6_mcp`: `uv run community_contributions/Vagz1216_us_equities_crypto/trading_floor.py`

## Notes

- Prices are in **USD**.
- Crypto can trade 24/7, but the run loop still follows class market-hours behavior unless `RUN_EVEN_WHEN_MARKET_IS_CLOSED=true`.
- If external APIs fail, fallback values are used so the simulation keeps running.

---

## Week 6 Checklist (implemented)

- [x] Built inside `6_mcp/community_contributions/...` (instructor path)
- [x] Uses OpenAI Agents SDK orchestration
- [x] Uses MCP servers/tools pattern for trading and research
- [x] Extended market tools for second asset class (crypto)
- [x] Updated prompts/instructions for multi-asset research/trading decisions
- [x] Preserved account tools and tracing flow
- [x] Added UI changes reflecting both asset classes
- [x] Added run instructions and assumptions
- [x] Added `reset.py` + `SETUP.md` so reviewers can reproduce after clone
- [x] Aligned `6_mcp/reset.py` strategy text with multi-asset (equities + crypto)
