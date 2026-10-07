"""Tools for the Sidekick: a mix of MCP servers, ready-made LangChain tools and our own."""

import asyncio
import os
import smtplib

from contextlib import AsyncExitStack
from datetime import date, datetime
from email.message import EmailMessage
from typing import Literal, Optional
from zoneinfo import ZoneInfo

import caldav
import requests
import wikipedia

from dotenv import load_dotenv
from langchain_community.tools import GoogleSerperRun, WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper, WikipediaAPIWrapper
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from pydantic import BaseModel, Field
from datetime import date, datetime, timedelta

load_dotenv(override=True)

# Wikimedia rejects the wikipedia library's default user agent, so identify ourselves properly
wikipedia.set_user_agent("agentic-track-course (https://edwarddonner.com)")

search = GoogleSerperRun(api_wrapper=GoogleSerperAPIWrapper())

wikipedia_lookup = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

ICLOUD_CALENDARS = {
    "Family Calendar",
    "Private bork",
}

def get_icloud_calendars():
    """Connect to iCloud CalDAV and return the configured calendars."""

    username = os.getenv("ICLOUD_USERNAME")
    password = os.getenv("ICLOUD_APP_PASSWORD")

    if not username:
        raise ValueError("ICLOUD_USERNAME is not configured in .env")

    if not password:
        raise ValueError("ICLOUD_APP_PASSWORD is not configured in .env")

    client = caldav.DAVClient(
        url="https://caldav.icloud.com",
        username=username,
        password=password,
    )

    principal = client.principal()
    calendars = principal.calendars()

    wanted = {
        name.strip().casefold()
        for name in ICLOUD_CALENDARS
    }

    selected = [
        calendar
        for calendar in calendars
        if calendar.get_display_name().strip().casefold() in wanted
    ]

    if not selected:
        raise RuntimeError(
            "None of the configured iCloud calendars were found."
        )

    return selected

@tool
def check_calendar_availability(
    start: str,
    end: str,
    timezone: str = "Asia/Singapore",
) -> dict:
    """
    Check selected iCloud calendars for timed events that overlap a proposed
    timed period.

    Only use this tool when both start and end contain specific times.

    Do not use this tool for:
    - all-day events
    - date-only events
    - candidates with no start time
    - candidates with no end time

    This tool is read-only and does not create, modify, or delete events.
    """

    try:
        query_tz = ZoneInfo(timezone)
    except Exception as exc:
        raise ValueError(
            f"Invalid IANA timezone: {timezone}"
        ) from exc

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    if start_dt.tzinfo is None or end_dt.tzinfo is None:
        raise ValueError(
            "start and end must include timezone offsets"
        )

    start_dt = start_dt.astimezone(query_tz)
    end_dt = end_dt.astimezone(query_tz)

    calendars = get_icloud_calendars()

    conflicts = []

    for calendar in calendars:
        events = calendar.search(
            start=start_dt,
            end=end_dt,
            event=True,
            expand=True,
        )

        for event in events:
            vevent = event.icalendar_component

            summary = str(
                vevent.get("summary", "Untitled event")
            )

            dtstart = vevent.decoded("dtstart")
            dtend = vevent.decoded("dtend")

            # All-day events do not block normal timed availability.
            if isinstance(dtstart, date) and not isinstance(dtstart, datetime):
                continue

            event_start = dtstart.astimezone(query_tz)
            event_end = dtend.astimezone(query_tz)

            if event_start < end_dt and event_end > start_dt:
                conflicts.append({
                    "title": summary,
                    "calendar": calendar.get_display_name().strip(),
                    "start": event_start.isoformat(),
                    "end": event_end.isoformat(),
                })

    return {
        "available": len(conflicts) == 0,
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "timezone": timezone,
        "calendars_checked": [
            calendar.get_display_name().strip()
            for calendar in calendars
        ],
        "conflicts": conflicts,
    }

@tool
def send_push_notification(message: str) -> str:
    """Send a push notification using the configured Pushover account."""

    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")

    if not token:
        raise ValueError("PUSHOVER_TOKEN is not configured in .env")

    if not user:
        raise ValueError("PUSHOVER_USER is not configured in .env")

    response = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": token,
            "user": user,
            "message": message,
        },
        timeout=10,
    )

    response.raise_for_status()

    return "Push notification sent successfully"

@tool
def send_email(subject: str, body: str) -> str:
    """Send an email to the user's configured EMAIL_ADDRESS."""

    email_address = os.getenv("EMAIL_ADDRESS")
    app_password = os.getenv("EMAIL_APP_PASSWORD")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")

    if not email_address:
        raise ValueError("EMAIL_ADDRESS is not configured in .env")

    if not app_password:
        raise ValueError("EMAIL_APP_PASSWORD is not configured in .env")

    message = EmailMessage()
    message["From"] = email_address
    message["To"] = email_address
    message["Subject"] = subject

    signature = "\n\n—\nSent by Max's Sidekick, Popeye ⚓"
    message.set_content(body + signature)

    with smtplib.SMTP_SSL(smtp_server, 465) as smtp:
        smtp.login(email_address, app_password)
        smtp.send_message(message)

    return "Email sent successfully to the user's configured EMAIL_ADDRESS"

@tool
def request_human_help(instructions: str) -> str:
    """Ask the user to do something in the browser window that you cannot do yourself,
    such as logging in to a site, passing a captcha, or approving two-factor authentication.
    Explain exactly what you need them to do. The run pauses until they have done it."""
    return "The user says it is done. Continue with the task."


def mcp_connections(sandbox: str) -> dict:
    """The MCP servers the Sidekick uses: a headed browser and a sandbox filesystem."""
    return {
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest", "--isolated"],
        },
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox],
        },
    }

def mcp_connections(sandbox: str) -> dict:
    """The MCP servers the Sidekick uses."""

    return {
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest", "--isolated"],
        },

        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                sandbox,
            ],
        },

        "whatsapp": {
            "transport": "stdio",
            "command": "uv",
            "args": [
                "--directory",
                "/Users/osmaxhartvigsen/Projects/whatsapp-mcp/whatsapp-mcp-server",
                "run",
                "main.py",
            ],
        },
    }

class CalendarCandidate(BaseModel):
    action_type: Literal["calendar_event", "reminder", "ignore"] = Field(
        description="Whether the message should become a calendar event, reminder, or be ignored."
    )

    title: str

    start: Optional[str] = Field(
        default=None,
        description="ISO 8601 start datetime including timezone offset, or YYYY-MM-DD for date-only events."
    )

    end: Optional[str] = Field(
        default=None,
        description="ISO 8601 end datetime including timezone offset."
    )

    timezone: str = Field(
        description="IANA timezone, for example Asia/Singapore or Europe/Oslo."
    )

    timezone_source: Literal["explicit", "inferred", "default"] = Field(
        default="default",
        description="How the timezone was determined."
    )

    all_day: bool = Field(
        default=False,
        description="True when the item is an all-day or date-only event."
    )

    location: Optional[str] = None
    notes: Optional[str] = None

    source: str = "WhatsApp"

    confidence: Literal["high", "medium", "low"]


@tool
def create_calendar_event(
    title: str,
    start: str,
    calendar_name: str,
    end: Optional[str] = None,
    timezone: str = "Asia/Singapore",
    all_day: bool = False,
    location: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    Create an event in one of the user's configured iCloud calendars.

    This is a write action and should only be called after user approval.

    For all-day/date-only events:
    - all_day=True
    - start must be YYYY-MM-DD
    - end may be omitted

    For timed events:
    - all_day=False
    - start and end must both be ISO 8601 datetimes
    - both must include timezone offsets
    """

    calendars = get_icloud_calendars()

    target = None

    wanted = calendar_name.strip().casefold()

    for calendar in calendars:
        if calendar.get_display_name().strip().casefold() == wanted:
            target = calendar
            break

    if target is None:
        raise ValueError(
            f"Calendar '{calendar_name}' was not found. "
            f"Available calendars: "
            f"{[c.get_display_name().strip() for c in calendars]}"
        )

    if all_day:
        start_date = date.fromisoformat(start)

        if end:
            end_date = date.fromisoformat(end)
        else:
            # CalDAV all-day events use an exclusive end date
            from datetime import timedelta
            end_date = start_date + timedelta(days=1)

        event = target.save_event(
            dtstart=start_date,
            dtend=end_date,
            summary=title,
            location=location,
            description=notes,
        )

    else:
        if not end:
            raise ValueError(
                "Timed calendar events require an end datetime."
            )

        query_tz = ZoneInfo(timezone)

        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)

        if start_dt.tzinfo is None or end_dt.tzinfo is None:
            raise ValueError(
                "Timed start and end must include timezone offsets."
            )

        start_dt = start_dt.astimezone(query_tz)
        end_dt = end_dt.astimezone(query_tz)

        if end_dt <= start_dt:
            raise ValueError(
                "Event end must be after event start."
            )

        event = target.save_event(
            dtstart=start_dt,
            dtend=end_dt,
            summary=title,
            location=location,
            description=notes,
        )

    return {
        "created": True,
        "title": title,
        "calendar": target.get_display_name().strip(),
        "start": start,
        "end": end,
        "timezone": timezone,
        "all_day": all_day,
        "location": location,
        "event_url": str(event.url) if getattr(event, "url", None) else None,
    }


@tool
def prepare_calendar_candidate(
    action_type: Literal["calendar_event", "reminder", "ignore"],
    title: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    timezone: str = "Asia/Singapore",
    timezone_source: Literal["explicit", "inferred", "default"] = "default",
    all_day: bool = False,
    location: Optional[str] = None,
    notes: Optional[str] = None,
    confidence: Literal["high", "medium", "low"] = "medium",
) -> dict:
    """
    Prepare and validate a potential calendar event or reminder extracted
    from a message.

    This tool does not create or modify a calendar event. It only returns
    a structured calendar candidate for later review and approval.
    """

    candidate = CalendarCandidate(
        action_type=action_type,
        title=title,
        start=start,
        end=end,
        timezone=timezone,
        timezone_source=timezone_source,
        all_day=all_day,
        location=location,
        notes=notes,
        confidence=confidence,
    )

    return candidate.model_dump()


class McpSessions:
    """Holds persistent MCP sessions open so the browser keeps its state between tool calls.

    The stdio transport must be opened and closed from the same asyncio task, so one
    background task owns the sessions: it opens them, waits, and unwinds them when stop()
    is called. Stopping shuts down the servers, and you will see the browser close.
    """

    def __init__(self, connections: dict):
        self.connections = connections
        self.tools = []
        self._ready = asyncio.Event()
        self._stop = asyncio.Event()
        self._task = None


    async def _run(self):
        client = MultiServerMCPClient(self.connections)

        async with AsyncExitStack() as stack:
            for name in self.connections:
                print(f"\n>>> Starting MCP server: {name}")

                session = await stack.enter_async_context(client.session(name))
                print(f">>> Connected to MCP server: {name}")

                tools = await load_mcp_tools(session, server_name=name)
                print(f">>> Loaded {len(tools)} tools from: {name}")

                self.tools += tools

            print(f"\n>>> All MCP servers ready — {len(self.tools)} MCP tools loaded")
            self._ready.set()
            await self._stop.wait()

    async def start(self) -> list:
        self._task = asyncio.create_task(self._run())
        ready = asyncio.create_task(self._ready.wait())
        await asyncio.wait([ready, self._task], return_when=asyncio.FIRST_COMPLETED)
        ready.cancel()
        if self._task.done():
            self._task.result()  # the servers failed to start; raise the real error
        return self.tools

    def stop(self):
        self._stop.set()


async def get_all_tools(sandbox: str):
    """Return the full tool list and MCP sessions."""

    print(">>> get_all_tools: creating MCP sessions")

    sessions = McpSessions(mcp_connections(sandbox))

    print(">>> get_all_tools: starting MCP servers")
    mcp_tools = await sessions.start()

    print(f">>> get_all_tools: loaded {len(mcp_tools)} MCP tools")

    our_tools = [
        search,
        send_push_notification,
        wikipedia_lookup,
        request_human_help,
        send_email,
        prepare_calendar_candidate,
        check_calendar_availability,
        create_calendar_event,
    ]

    print(f">>> get_all_tools: loaded {len(our_tools)} local tools")

    return our_tools + mcp_tools, sessions
