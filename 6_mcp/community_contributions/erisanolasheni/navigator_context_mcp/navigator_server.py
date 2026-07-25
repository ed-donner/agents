"""MCP server: keep problem statement, success metric, and session notes for agent workflows.

Inspired by Week 6 capstone patterns and the course closing themes: start from the problem,
define how you will know you succeeded, log what you try (R&D notes), and pull a compact
briefing into the prompt when needed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

_STATE_FILE = Path(__file__).resolve().parent / ".navigator_state.json"
mcp = FastMCP("navigator_context")


def _load() -> dict[str, Any]:
    if not _STATE_FILE.exists():
        return {"problem": "", "metric": "", "notes": []}
    try:
        return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"problem": "", "metric": "", "notes": []}


def _save(data: dict[str, Any]) -> None:
    _STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


@mcp.tool()
async def set_problem_statement(statement: str) -> str:
    """Record the problem you are solving (start from the problem, not from 'I want an agent')."""
    data = _load()
    data["problem"] = statement.strip()
    _save(data)
    return "Problem statement updated."


@mcp.tool()
async def set_success_metric(metric: str) -> str:
    """Record the north-star metric or observable signal that means the problem is solved."""
    data = _load()
    data["metric"] = metric.strip()
    _save(data)
    return "Success metric updated."


@mcp.tool()
async def append_session_note(note: str) -> str:
    """Append a timestamped note (experiment outcome, trace observation, prompt tweak, etc.)."""
    data = _load()
    notes = data.setdefault("notes", [])
    notes.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "text": note.strip(),
        }
    )
    # avoid unbounded growth for local JSON file
    data["notes"] = notes[-500:]
    _save(data)
    return "Note recorded."


@mcp.tool()
async def list_session_notes(limit: int = 15) -> str:
    """Return the most recent session notes (newest last), up to `limit` entries."""
    data = _load()
    notes = data.get("notes") or []
    if limit < 1:
        limit = 1
    slice_ = notes[-limit:]
    if not slice_:
        return "(no notes yet)"
    lines = [f"[{n['ts']}] {n['text']}" for n in slice_]
    return "\n".join(lines)


@mcp.tool()
async def get_briefing_for_prompt() -> str:
    """Return a short block of text suitable to paste into a system or developer prompt."""
    data = _load()
    problem = (data.get("problem") or "").strip() or "(not set — use set_problem_statement)"
    metric = (data.get("metric") or "").strip() or "(not set — use set_success_metric)"
    notes = data.get("notes") or []
    recent = notes[-5:]
    note_lines = (
        "\n".join(f"- [{n['ts']}] {n['text']}" for n in recent)
        if recent
        else "- (no session notes yet)"
    )
    return (
        "### Project navigator context\n"
        f"**Problem:** {problem}\n"
        f"**Success signal:** {metric}\n"
        "**Recent session notes:**\n"
        f"{note_lines}\n"
    )


@mcp.tool()
async def clear_navigator_state(confirm: bool = False) -> str:
    """Reset stored problem, metric, and notes. Must pass confirm=true."""
    if not confirm:
        return "Refused: pass confirm=true to clear all navigator state."
    _save({"problem": "", "metric": "", "notes": []})
    return "Navigator state cleared."


if __name__ == "__main__":
    mcp.run(transport="stdio")
