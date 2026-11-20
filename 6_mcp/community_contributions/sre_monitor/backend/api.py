"""Read-only HTTP API and dashboard over the monitor's database.

The engine writes the database; this only reads it. From the sre_monitor directory:

    uv run uvicorn backend.api:app --port 8100
"""

import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from . import store
from .agents import REPORTS_DIR
from .settings import get_settings, model_label

DASHBOARD = Path(__file__).resolve().parent / "dashboard.html"
REPORT_NAME = re.compile(r"^postmortem-[\d-]+\.md$")

app = FastAPI(title="SRE Monitor")


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD.read_text()


@app.get("/api/overview")
def overview() -> dict:
    settings = get_settings()
    stored = store.services()
    services = []
    for service in settings.services:
        row = stored.get(service.name) or {"indicator": "pending", "description": "Not checked yet"}
        services.append({**row, "name": service.name, "url": service.url})
    return {
        "model": model_label(),
        "poll_interval_minutes": settings.monitor.poll_interval_minutes,
        "daily_review_hour": settings.monitor.daily_review_hour,
        "last_poll": store.get_meta("last_poll"),
        "last_daily_review": store.get_meta("last_daily_review"),
        "services": services,
    }


@app.get("/api/incidents")
def incidents(hours: int = 24) -> dict:
    return {"active": store.active_incidents(), "recent": store.incidents_since(hours)}


@app.get("/api/activity")
def activity(limit: int = 80) -> list[dict]:
    return store.recent_activity(limit)


@app.get("/api/emails")
def emails(limit: int = 30) -> list[dict]:
    return store.recent_emails(limit)


@app.get("/api/reports")
def reports() -> list[str]:
    if not REPORTS_DIR.exists():
        return []
    return sorted((path.name for path in REPORTS_DIR.glob("postmortem-*.md")), reverse=True)


@app.get("/api/reports/{name}", response_class=PlainTextResponse)
def report(name: str) -> str:
    path = REPORTS_DIR / name
    if not REPORT_NAME.match(name) or not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return path.read_text()
