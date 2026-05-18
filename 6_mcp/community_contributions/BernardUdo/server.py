"""stdio MCP server: IANA timezone search and local/UTC time helpers (stdlib only)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo, available_timezones

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("bernard_timezone_mcp")


def _zone_or_raise(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name.strip())
    except Exception as e:
        raise ValueError(
            f"Invalid IANA timezone {name!r}. Use search_timezones(prefix) to find valid names."
        ) from e


@mcp.tool()
def search_timezones(prefix: str = "", limit: int = 40) -> list[str]:
    """
    List IANA timezone names matching a case-insensitive substring (e.g. 'Europe', 'Lagos').
    """
    if limit < 1 or limit > 200:
        limit = 40
    p = prefix.strip().lower()
    out: list[str] = []
    for z in sorted(available_timezones()):
        if not p or p in z.lower():
            out.append(z)
        if len(out) >= limit:
            break
    return out


@mcp.tool()
def now_in_zone(timezone: str) -> dict[str, Any]:
    """Current local time and UTC offset for an IANA timezone name."""
    zi = _zone_or_raise(timezone)
    now = datetime.now(zi)
    off = now.utcoffset()
    off_s = off.total_seconds() if off else 0.0
    return {
        "timezone": str(zi),
        "local_iso": now.isoformat(),
        "utc_offset_hours": round(off_s / 3600.0, 4),
    }


@mcp.tool()
def utc_to_zone(utc_iso: str, timezone: str) -> dict[str, Any]:
    """
    Parse a UTC instant (ISO 8601 with Z or +00:00) and show it in the target IANA zone.
    """
    zi = _zone_or_raise(timezone)
    raw = utc_iso.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    local = dt.astimezone(zi)
    return {
        "input_utc_iso": dt.isoformat(),
        "timezone": str(zi),
        "local_iso": local.isoformat(),
    }


@mcp.resource("tz://about")
def about_timezone_mcp() -> str:
    return (
        "BernardUdo timezone MCP: tools search_timezones, now_in_zone, utc_to_zone. "
        "Uses Python zoneinfo only; no network calls."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
