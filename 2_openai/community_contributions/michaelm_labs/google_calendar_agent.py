#!/usr/bin/env python3
"""
Calendar Agent — adds appointments to Google Calendar using Claude tool-use
and the Google Calendar REST API directly.

FIRST-TIME SETUP
----------------
1. Go to https://console.cloud.google.com/
2. Create a project (or select one).
3. Enable the Google Calendar API.
4. Create OAuth 2.0 credentials (Desktop app).
5. Copy the client ID and secret into your .env file (see ENV VARS below).
6. Run once — a browser window will open for you to authorise access.
   Tokens are saved to token.json; subsequent runs use them automatically.

ENV VARS (.env file)
--------------------
    CLAUDE_API_KEY      your Anthropic API key
    GOOGLE_CLIENT_ID       OAuth 2.0 client ID from Google Cloud Console
    GOOGLE_CLIENT_SECRET   OAuth 2.0 client secret from Google Cloud Console
    GOOGLE_PROJECT_ID      your Google Cloud project ID

.GITIGNORE
----------
    .env
    token.json

USAGE
-----
    python3 calendar_agent.py "Dentist on 25 June at 2pm for 1 hour"
    python3 calendar_agent.py        # interactive mode
"""

import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv(override=True)

def _require_env(key: str, hint: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"{key} not found in .env — {hint}")
    return val

CLAUDE_API_KEY    = _require_env("CLAUDE_API_KEY",    "add your Anthropic API key")
GOOGLE_CLIENT_ID     = _require_env("GOOGLE_CLIENT_ID",     "copy from Google Cloud Console → Credentials")
GOOGLE_CLIENT_SECRET = _require_env("GOOGLE_CLIENT_SECRET", "copy from Google Cloud Console → Credentials")
GOOGLE_PROJECT_ID    = _require_env("GOOGLE_PROJECT_ID",    "your Google Cloud project ID")

MODEL      = "claude-sonnet-4-20250514"
SCOPES     = ["https://www.googleapis.com/auth/calendar.events"]
TOKEN_FILE = Path(__file__).parent / "token.json"
CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

SYSTEM_PROMPT = """You are a calendar assistant. Your only job is to add appointments to the user's Google Calendar.

When the user describes an appointment:
1. Extract: summary (title), start datetime, end datetime, location (if any), description (if any).
2. Today is Saturday 7 June 2026, timezone Europe/London (UTC+1). Resolve relative dates accordingly.
3. Always use ISO 8601 format with timezone offset for datetimes, e.g. 2026-06-25T14:00:00+01:00
4. Call the create_calendar_event tool, then confirm in one short sentence what was created.

If critical information is missing (e.g. no time given), ask one concise clarifying question first.
Do not explain your reasoning — just act."""

# ---------------------------------------------------------------------------
# Tool definition (passed to Claude)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "create_calendar_event",
        "description": "Creates an event in the user's primary Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Title of the event."
                },
                "start_datetime": {
                    "type": "string",
                    "description": "Start time in ISO 8601 format with timezone, e.g. 2026-06-25T14:00:00+01:00"
                },
                "end_datetime": {
                    "type": "string",
                    "description": "End time in ISO 8601 format with timezone, e.g. 2026-06-25T15:00:00+01:00"
                },
                "location": {
                    "type": "string",
                    "description": "Optional location of the event."
                },
                "description": {
                    "type": "string",
                    "description": "Optional description or notes for the event."
                },
            },
            "required": ["summary", "start_datetime", "end_datetime"],
        },
    }
]

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_credentials() -> Credentials:
    """Return valid Google OAuth credentials, refreshing or re-authorising as needed."""
    creds: Credentials | None = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing Google access token...")
            creds.refresh(Request())
        else:
            print("🌐 Opening browser for Google authorisation...")
            client_config = {
                "installed": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "project_id": GOOGLE_PROJECT_ID,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost"],
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())
        print(f"✅ Tokens saved to {TOKEN_FILE}\n")

    return creds

# ---------------------------------------------------------------------------
# Calendar API call
# ---------------------------------------------------------------------------

def create_calendar_event(creds: Credentials, params: dict) -> dict:
    """Call the Google Calendar REST API to create an event. Returns the created event."""

    # Refresh token if needed before making the API call
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())

    event_body = {
        "summary": params["summary"],
        "start": {"dateTime": params["start_datetime"], "timeZone": "Europe/London"},
        "end":   {"dateTime": params["end_datetime"],   "timeZone": "Europe/London"},
    }
    if params.get("location"):
        event_body["location"] = params["location"]
    if params.get("description"):
        event_body["description"] = params["description"]

    response = requests.post(
        f"{CALENDAR_API_BASE}/calendars/primary/events",
        headers={"Authorization": f"Bearer {creds.token}"},
        json=event_body,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

def run_agent(user_request: str, creds: Credentials) -> None:
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    messages = [{"role": "user", "content": user_request}]

    print(f"\n📅 Request: {user_request}\n")

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Print any text Claude produced
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"🤖 {block.text}")

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                print(f"🔧 Calling: {block.name}")
                print(f"   {json.dumps(block.input, indent=2)}")

                if block.name == "create_calendar_event":
                    try:
                        event = create_calendar_event(creds, block.input)
                        result = {
                            "status": "created",
                            "event_id": event.get("id"),
                            "html_link": event.get("htmlLink"),
                            "summary": event.get("summary"),
                            "start": event.get("start"),
                            "end": event.get("end"),
                        }
                        print(f"   ✅ Event created: {event.get('htmlLink')}")
                    except requests.HTTPError as e:
                        result = {"status": "error", "message": str(e)}
                        print(f"   ❌ API error: {e}")
                else:
                    result = {"status": "error", "message": f"Unknown tool: {block.name}"}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

            messages.append({"role": "user", "content": tool_results})
            continue

        # Any other stop reason — exit
        break

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    creds = get_credentials()

    if len(sys.argv) > 1:
        run_agent(" ".join(sys.argv[1:]), creds)
    else:
        print("📅 Calendar Agent — describe your appointment (or 'quit' to exit)\n")
        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("quit", "exit", "q"):
                    print("Bye!")
                    break
                run_agent(user_input, creds)
                print()
            except (KeyboardInterrupt, EOFError):
                print("\nBye!")
                break

if __name__ == "__main__":
    main()