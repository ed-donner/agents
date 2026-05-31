"""
Habit streak MCP server (stdio). Persists to habits_data.json next to this file.
Log to stderr only — stdout is reserved for MCP JSON-RPC.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [habit_mcp] %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("habit_mcp")

_ROOT = Path(__file__).resolve().parent
_DATA_FILE = _ROOT / "habits_data.json"

mcp = FastMCP("habit_streak")


def _load() -> dict[str, Any]:
    if not _DATA_FILE.is_file():
        return {"entries": []}
    try:
        return json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Resetting corrupt data file: %s", e)
        return {"entries": []}


def _save(data: dict[str, Any]) -> None:
    _DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _norm_name(name: str) -> str:
    return (name or "").strip().lower()


def _today_iso() -> str:
    return date.today().isoformat()


@mcp.tool()
async def log_habit(name: str, done: bool, note: str = "") -> dict[str, Any]:
    """Append a habit check-in for today (local date). Same habit can be logged once per day; later call overwrites that day.

    Args:
        name: Habit label, e.g. "walk", "read".
        done: True if completed today.
        note: Optional short note.
    """
    key = _norm_name(name)
    if not key:
        return {"ok": False, "error": "name is required"}

    data = _load()
    entries: list = data.setdefault("entries", [])
    today = _today_iso()

    replaced = False
    for e in entries:
        if e.get("name") == key and e.get("date") == today:
            e["done"] = bool(done)
            e["note"] = (note or "").strip()
            replaced = True
            break
    if not replaced:
        entries.append(
            {
                "date": today,
                "name": key,
                "done": bool(done),
                "note": (note or "").strip(),
            }
        )

    _save(data)
    logger.info("log_habit %s done=%s date=%s", key, done, today)
    return {
        "ok": True,
        "habit": key,
        "date": today,
        "done": bool(done),
        "note": (note or "").strip(),
        "overwrote_today": replaced,
    }


@mcp.tool()
async def list_habits() -> list[str]:
    """Return distinct habit names seen in the log (sorted)."""
    data = _load()
    names = {str(e.get("name", "")).lower() for e in data.get("entries", []) if e.get("name")}
    return sorted(names)


@mcp.tool()
async def streak(name: str) -> dict[str, Any]:
    """Current strict streak: consecutive calendar days ending today where the habit was logged with done=True. A day with no entry or done=False breaks the streak.

    Args:
        name: Habit name (case-insensitive).
    """
    key = _norm_name(name)
    if not key:
        return {"habit": "", "streak_days": 0, "error": "name is required"}

    data = _load()
    by_date: dict[str, bool] = {}
    for e in data.get("entries", []):
        if str(e.get("name", "")).lower() != key:
            continue
        d = e.get("date")
        if not d:
            continue
        by_date[str(d)] = bool(e.get("done", False))

    d = date.today()
    count = 0
    while True:
        ds = d.isoformat()
        if ds not in by_date:
            break
        if not by_date[ds]:
            break
        count += 1
        d = d - timedelta(days=1)

    return {"habit": key, "streak_days": count, "as_of": _today_iso()}


@mcp.tool()
async def recent_days(name: str, days: int = 7) -> list[dict[str, Any]]:
    """Last N calendar days (including today) for one habit: date, done (null if no log), note."""
    key = _norm_name(name)
    if not key:
        return []

    n = max(1, min(int(days), 90))
    data = _load()
    by_date: dict[str, dict] = {}
    for e in data.get("entries", []):
        if str(e.get("name", "")).lower() != key:
            continue
        d = e.get("date")
        if not d:
            continue
        by_date[str(d)] = {
            "date": str(d),
            "done": bool(e.get("done", False)),
            "note": str(e.get("note", "")),
        }

    out: list[dict[str, Any]] = []
    for i in range(n - 1, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        if d in by_date:
            out.append(by_date[d])
        else:
            out.append({"date": d, "done": None, "note": ""})
    return out


if __name__ == "__main__":
    mcp.run(transport="stdio")
