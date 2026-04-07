"""
MCP server: append-only paper trading journal (no real execution).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("paper_ledger")

_ROOT = Path(__file__).resolve().parent
_DATA = _ROOT / "data"
_STATE = _DATA / "paper_state.json"


def _load() -> dict:
    _DATA.mkdir(parents=True, exist_ok=True)
    if not _STATE.exists():
        state = {"positions": {}, "journal": []}
        _STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state
    return json.loads(_STATE.read_text(encoding="utf-8"))


def _save(state: dict) -> None:
    _STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


@mcp.tool()
async def get_paper_portfolio() -> str:
    """Return current paper positions and recent journal entries."""
    state = _load()
    return json.dumps(state, indent=2)


@mcp.tool()
async def propose_paper_order(
    venue: str,
    symbol: str,
    side: str,
    quantity: float,
    rationale: str,
    routing_context: str,
) -> str:
    """Record a paper intent (does not execute anywhere). routing_context should summarize venue scores."""
    state = _load()
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "venue": venue,
        "symbol": symbol.strip().upper(),
        "side": side.strip().lower(),
        "quantity": float(quantity),
        "rationale": rationale,
        "routing_context": routing_context[:4000],
    }
    state["journal"].append(entry)
    key = f"{venue}:{entry['symbol']}"
    pos = state["positions"].get(key, {"qty": 0.0})
    q = float(quantity)
    if side.lower() == "buy":
        pos["qty"] = float(pos["qty"]) + q
    else:
        pos["qty"] = float(pos["qty"]) - q
    state["positions"][key] = pos
    _save(state)
    return json.dumps({"status": "recorded", "entry": entry, "positions": state["positions"]}, indent=2)


@mcp.resource("paper://state")
async def paper_resource() -> str:
    return json.dumps(_load(), indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
