"""
Athlete Travel Companion — MCP server (stdio) exposing tools for training, travel, and connectivity.

Used with OpenAI Agents SDK + MCPServerStdio.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
CALENDAR_PATH = DATA_DIR / "travel_calendar.json"
LOG_PATH = DATA_DIR / "workout_log.jsonl"

mcp = FastMCP("athlete_travel_companion")


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CALENDAR_PATH.exists():
        CALENDAR_PATH.write_text(
            json.dumps(
                [
                    {
                        "title": "Easy run — hotel loop",
                        "start": (datetime.now(timezone.utc) + timedelta(days=1)).strftime(
                            "%Y-%m-%dT07:00:00Z"
                        ),
                        "end": (datetime.now(timezone.utc) + timedelta(days=1)).strftime(
                            "%Y-%m-%dT08:00:00Z"
                        ),
                        "notes": "Placeholder — replace with your real schedule.",
                    }
                ],
                indent=2,
            ),
            encoding="utf-8",
        )


@mcp.tool()
async def get_training_weather(city: str, country_code: str = "") -> str:
    """Current weather and short forecast for training decisions (heat, wind, rain).

    Uses OpenWeatherMap. Pass city like 'Boulder' or 'Paris, FR'.
    """
    key = os.environ.get("OPENWEATHERMAP_API_KEY")
    if not key:
        return json.dumps({"error": "Set OPENWEATHERMAP_API_KEY in the environment."})

    q = f"{city},{country_code}" if country_code else city
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": q, "appid": key, "units": "metric"},
        )
        if r.status_code != 200:
            return json.dumps({"error": r.text[:500]})
        cur = r.json()

        r2 = await client.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"q": q, "appid": key, "units": "metric", "cnt": 8},
        )
        fc = r2.json() if r2.status_code == 200 else {}

    out: dict[str, Any] = {
        "location_query": q,
        "current": {
            "temp_c": cur.get("main", {}).get("temp"),
            "feels_like_c": cur.get("main", {}).get("feels_like"),
            "humidity_pct": cur.get("main", {}).get("humidity"),
            "wind_m_s": cur.get("wind", {}).get("speed"),
            "description": (cur.get("weather") or [{}])[0].get("description"),
        },
        "forecast_24h_summary": [],
    }
    for step in (fc.get("list") or [])[:6]:
        out["forecast_24h_summary"].append(
            {
                "time_utc": step.get("dt_txt"),
                "temp_c": step.get("main", {}).get("temp"),
                "pop": step.get("pop"),
                "description": (step.get("weather") or [{}])[0].get("description"),
            }
        )
    return json.dumps(out, indent=2)


@mcp.tool()
async def geocode_city(city: str, country_code: str = "") -> str:
    """Resolve a city name to lat/lon using OpenWeatherMap geocoding (needs OPENWEATHERMAP_API_KEY)."""
    key = os.environ.get("OPENWEATHERMAP_API_KEY")
    if not key:
        return json.dumps({"error": "Set OPENWEATHERMAP_API_KEY."})
    q = f"{city},{country_code}" if country_code else city
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": q, "limit": 1, "appid": key},
        )
    if r.status_code != 200:
        return json.dumps({"error": r.text[:300]})
    data = r.json()
    if not data:
        return json.dumps({"error": "No results", "query": q})
    loc = data[0]
    return json.dumps(
        {
            "name": loc.get("name"),
            "lat": loc.get("lat"),
            "lon": loc.get("lon"),
            "country": loc.get("country"),
        },
        indent=2,
    )


@mcp.tool()
async def get_elevation_meters(latitude: float, longitude: float) -> str:
    """Approximate ground elevation (m) for altitude-aware training load — uses Open-Elevation API (no key)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.open-elevation.com/api/v1/lookup",
                json={"locations": [{"latitude": latitude, "longitude": longitude}]},
            )
        r.raise_for_status()
        d = r.json()
        el = (d.get("results") or [{}])[0].get("elevation")
        return json.dumps({"elevation_m": el, "lat": latitude, "lon": longitude}, indent=2)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)})


@mcp.tool()
async def search_places_for_training(
    query: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> str:
    """Find gyms, tracks, or running-friendly venues via Google Places Text Search.

    Requires GOOGLE_MAPS_API_KEY with Places API enabled. Example query: 'running track' or '24 hour gym'.
    If latitude/longitude are provided, bias search near that point.
    """
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        return json.dumps(
            {
                "error": "Set GOOGLE_MAPS_API_KEY (Places API enabled) for place search.",
                "hint": "Enable Places API in Google Cloud Console for this key.",
            }
        )

    params: dict[str, Any] = {"query": query, "key": key}
    if latitude is not None and longitude is not None:
        params["location"] = f"{latitude},{longitude}"
        params["radius"] = 15000

    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params,
        )
    data = r.json()
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        return json.dumps({"error": data.get("status"), "message": data.get("error_message")})

    results = []
    for p in (data.get("results") or [])[:8]:
        loc = p.get("geometry", {}).get("location", {})
        results.append(
            {
                "name": p.get("name"),
                "address": p.get("formatted_address"),
                "rating": p.get("rating"),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "place_id": p.get("place_id"),
            }
        )
    return json.dumps({"places": results}, indent=2)


@mcp.tool()
async def list_calendar_events(days_ahead: int = 7) -> str:
    """List upcoming training-related events from the local travel calendar file (JSON)."""
    _ensure_data_dir()
    try:
        raw = json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return json.dumps({"error": str(exc)})

    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=max(1, min(days_ahead, 30)))
    upcoming = []
    for ev in raw:
        try:
            start_s = ev.get("start", "")
            st = datetime.fromisoformat(start_s.replace("Z", "+00:00"))
            if now <= st <= horizon:
                upcoming.append(ev)
        except (ValueError, TypeError):
            upcoming.append(ev)
    return json.dumps({"events": upcoming}, indent=2)


@mcp.tool()
async def add_calendar_event(
    title: str,
    start_iso: str,
    end_iso: str,
    notes: str = "",
) -> str:
    """Add a training block to the local JSON calendar (ISO8601 times, Z suffix recommended)."""
    _ensure_data_dir()
    try:
        raw = json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        raw = []
    if not isinstance(raw, list):
        raw = []
    raw.append(
        {
            "title": title,
            "start": start_iso,
            "end": end_iso,
            "notes": notes,
        }
    )
    CALENDAR_PATH.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    return json.dumps({"ok": True, "count": len(raw)}, indent=2)


@mcp.tool()
async def append_workout_log(
    date_iso: str,
    session_type: str,
    duration_minutes: int,
    rpe_1_to_10: int,
    notes: str = "",
) -> str:
    """Append one workout line to JSONL performance log (RPE = rate of perceived exertion)."""
    _ensure_data_dir()
    line = {
        "date": date_iso,
        "session_type": session_type,
        "duration_minutes": duration_minutes,
        "rpe": rpe_1_to_10,
        "notes": notes,
        "logged_at": datetime.now(timezone.utc).isoformat(),
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    return json.dumps({"ok": True, "path": str(LOG_PATH)}, indent=2)


@mcp.tool()
async def read_recent_workout_log(lines: int = 20) -> str:
    """Read the last N lines from the workout JSONL log."""
    _ensure_data_dir()
    if not LOG_PATH.exists():
        return json.dumps({"entries": [], "message": "No log yet."})
    text = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    chunk = text[-max(1, min(lines, 100)) :]
    entries = []
    for ln in chunk:
        try:
            entries.append(json.loads(ln))
        except json.JSONDecodeError:
            entries.append({"raw": ln})
    return json.dumps({"entries": entries}, indent=2)


@mcp.tool()
async def send_telegram_message(text: str) -> str:
    """Send a short message via Telegram Bot API (for connecting with local athletes / coaches).

    Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (your chat with the bot).
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return json.dumps(
            {
                "error": "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.",
                "sent": False,
            }
        )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(url, json={"chat_id": chat, "text": text[:4000]})
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:500]}
    return json.dumps({"http_status": r.status_code, "response": body}, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
