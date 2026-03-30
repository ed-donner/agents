from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from allowlist import ALLOWED_HOSTS, is_allowed_host
from wellness_store import (
    append_journal,
    get_grounding,
    log_mood,
    recent_journal,
    recent_moods,
)

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent
CONTENT = BASE_DIR / "content"
SANDBOX = BASE_DIR / "sandbox"

mcp = FastMCP("wellness_server")

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


@mcp.tool()
async def log_mood_entry(user_id: str, score: int, note: str = "") -> str:
    """Log today's mood check-in. Score is 1 (low) through 5 (okay/positive).

    Args:
        user_id: Stable id for this person (e.g. default).
        score: Integer 1-5.
        note: Optional short note.
    """
    log_mood(user_id, score, note or None)
    return f"Logged mood {score} for {user_id.strip().lower()}."


@mcp.tool()
async def append_journal_entry(user_id: str, text: str) -> str:
    """Append a journal entry for the user (stored locally in SQLite).

    Args:
        user_id: Stable id for this person.
        text: Journal text; keep supportive and non-clinical—reflect user words.
    """
    append_journal(user_id, text)
    return "Journal entry saved."


@mcp.tool()
async def list_recent_mood_logs(user_id: str, limit: int = 14) -> str:
    """Return recent mood rows as readable text for the coach."""
    rows = recent_moods(user_id, min(limit, 100))
    if not rows:
        return "No mood entries yet."
    lines = [f"{t} | score={s} | {n or ''}" for t, s, n in rows]
    return "\n".join(lines)


@mcp.tool()
async def list_recent_journal_excerpts(user_id: str, limit: int = 8) -> str:
    """Return recent journal snippets newest-first."""
    rows = recent_journal(user_id, min(limit, 50))
    if not rows:
        return "No journal entries yet."
    parts = []
    for t, txt in rows:
        excerpt = (txt[:400] + "\u2026") if len(txt) > 400 else txt
        parts.append(f"--- {t} ---\n{excerpt}")
    return "\n\n".join(parts)


@mcp.tool()
async def get_grounding_exercise(kind: str) -> str:
    """Return a scripted grounding or sleep-hygiene routine (general wellness, not therapy).

    Args:
        kind: One of: breathing, 54321, sleep_hygiene
    """
    return get_grounding(kind)


@mcp.tool()
async def fetch_psychoeducation_page(url: str) -> str:
    """Fetch plain text from a psychoeducation URL. ONLY allowlisted government/nonprofit mental health hosts are permitted.

    Args:
        url: Full https URL. Host must be in the allowlist (nimh, nhs, who, apa, mhanational).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "Only http(s) URLs are allowed."
    host = (parsed.hostname or "").lower()
    if not is_allowed_host(host):
        return (
            f"Host not allowlisted: {host}. Allowed: {', '.join(sorted(ALLOWED_HOSTS))}. "
            "Do not guess other URLs."
        )
    try:
        r = httpx.get(
            url,
            timeout=20.0,
            follow_redirects=True,
            headers={"User-Agent": "WellnessCopilot/1.0 (psychoeducation; +local)"},
        )
        r.raise_for_status()
        text = r.text
        if len(text) > 12000:
            text = text[:12000] + "\n\n[truncated]"
        return text
    except Exception as e:
        return f"Fetch failed: {e!s}"


@mcp.tool()
async def export_week_summary_markdown(user_id: str, days: int = 7) -> str:
    """Write a simple markdown summary of recent moods and journal titles into sandbox/ for the user to open.

    Args:
        user_id: User id.
        days: Look back window (approximate—uses last N mood/journal rows).
    """
    SANDBOX.mkdir(parents=True, exist_ok=True)
    moods = recent_moods(user_id, 90)
    journals = recent_journal(user_id, 30)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SANDBOX / f"wellness_export_{user_id.strip().lower()}_{stamp}.md"
    lines = [
        f"# Wellness export — {user_id}",
        "",
        "## Recent moods",
    ]
    for t, s, n in moods[:30]:
        lines.append(f"- {t}: **{s}/5** {n or ''}")
    lines.extend(["", "## Recent journal (excerpts)"])
    for t, txt in journals[:15]:
        excerpt = txt[:300].replace("\n", " ")
        lines.append(f"- {t}: {excerpt}")
    path.write_text("\n".join(lines), encoding="utf-8")
    return f"Wrote {path.relative_to(BASE_DIR)} — open from the sandbox folder."


@mcp.tool()
async def send_gentle_reminder(message: str) -> str:
    """Send a short push notification if Pushover is configured (.env PUSHOVER_USER and PUSHOVER_TOKEN)."""
    user = os.getenv("PUSHOVER_USER")
    token = os.getenv("PUSHOVER_TOKEN")
    if not user or not token:
        return "Pushover not configured; set PUSHOVER_USER and PUSHOVER_TOKEN to enable."
    payload = {"user": user, "token": token, "message": message[:512]}
    requests.post(PUSHOVER_URL, data=payload, timeout=15)
    return "Reminder sent (if credentials valid)."


@mcp.resource("wellness://crisis")
async def crisis_resource() -> str:
    p = CONTENT / "crisis_resources.md"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return "Crisis resource file missing."


@mcp.resource("wellness://care_plan/{user_id}")
async def care_plan_resource(user_id: str) -> str:
    uid = user_id.strip().lower()
    user_file = CONTENT / f"care_plan_{uid}.md"
    if user_file.exists():
        return user_file.read_text(encoding="utf-8")
    default = CONTENT / "care_plan_default.md"
    if default.exists():
        return default.read_text(encoding="utf-8")
    return "No care plan content."


if __name__ == "__main__":
    mcp.run(transport="stdio")
