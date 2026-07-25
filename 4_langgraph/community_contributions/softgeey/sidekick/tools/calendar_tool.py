"""Google Calendar integration: read upcoming events."""

from datetime import datetime, timezone
from typing import Any
from googleapiclient.discovery import build
from google_auth import get_google_credentials


def _calendar_service() -> Any:
    creds = get_google_credentials()
    if not creds:
        raise RuntimeError("Google credentials not configured. See README for setup.")
    return build("calendar", "v3", credentials=creds)


def get_upcoming_events(max_results: int = 10, calendar_id: str = "primary") -> list[dict]:
    """
    Fetch upcoming calendar events starting from now.
    Returns list of {summary, start, end, location, description, attendees}.
    """
    service = _calendar_service()
    now = datetime.now(timezone.utc).isoformat()

    result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = []
    for item in result.get("items", []):
        start = item["start"].get("dateTime") or item["start"].get("date")
        end = item["end"].get("dateTime") or item["end"].get("date")
        attendees = [a.get("email", "") for a in item.get("attendees", [])]
        events.append(
            {
                "summary": item.get("summary", "(no title)"),
                "start": start,
                "end": end,
                "location": item.get("location", ""),
                "description": item.get("description", "")[:500],
                "attendees": attendees,
            }
        )
    return events
