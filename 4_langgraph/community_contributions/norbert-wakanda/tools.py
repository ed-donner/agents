import os
import datetime
import json
import time
from datetime import date
from typing import Dict, List, Optional
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

MAX_CONT = int(1500)

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")        # ← paste exactly
CLIENT_SECRET = os.getenv("GOOGLE_SECRET_KEY") 
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")     # ← paste exactly 

from langchain_core.tools import tool

@tool
def get_recent_files_context(directory:str=".", hours:int  =24)->List[Dict]:
    "Function to get the files modified by the user in the last 24 hours and return the content"

    allowed_extensions = (".md")
    recent_files = []
    cutoff_time = time.time() - hours * 3600

    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith(allowed_extensions):
                continue

            path = os.path.join(root, file)

            try:
                modified_time = os.path.getmtime(path)

                if modified_time < cutoff_time:
                    continue

                # Read file content
                if file.endswith(".py") or file.endswith(".md"):
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                elif file.endswith(".ipynb"):
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        notebook = json.load(f)

                    code_cells = []
                    for cell in notebook.get("cells", []):
                        if cell.get("cell_type") == "code":
                            code_cells.append("".join(cell.get("source", [])))

                    content = "\n\n".join(code_cells)

                # Limit context size
                content = content[:MAX_CONT]

                recent_files.append({
                    "file": path,
                    "modified_time": modified_time,
                    "content": content
                })

            except Exception as e:
                print("  Skipped:", path, "| Error:", str(e))
    return recent_files

@tool
def get_events_on_date(
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    max_results: int = 50
) -> list[dict]:
    """
    Fetch events on a specific date.
    If year/month/day are not provided → uses today's date.
    Use this tool when user asks about meetings, events, calendar, preparation, bootcamp etc.
    """
    if year is None or month is None or day is None:
        today = date.today()
        year = today.year
        month = today.month
        day = today.day

   
    year = year
    month = month
    day = day
    max_results  = max_results
 
    creds = None
    token_path = "token.json"
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
    CLIENT_CONFIG = {
    "installed": {
        "client_id": CLIENT_ID,
        "project_id": GOOGLE_PROJECT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": CLIENT_SECRET,
        "redirect_uris": ["http://localhost"]
    }
}

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        start_utc = datetime.datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
        end_utc = start_utc + datetime.timedelta(days=1)

        time_min = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        time_max = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=max_results
        ).execute()

        events = events_result.get("items", [])
        target_date = datetime.date(year, month, day)

        filtered_events = []

        for event in events:
            start_info = event.get("start", {})
            include = False

            if "dateTime" in start_info:
                dt_str = start_info["dateTime"]
                dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                if dt.date() == target_date:
                    include = True

            elif "date" in start_info:
                if start_info["date"] == target_date.isoformat():
                    include = True

            if include:
                filtered_events.append({
                    "summary": event.get("summary", "(no title)"),
                    "description": event.get("description", ""),
                    "start": event.get("start", {}).get("dateTime") or event.get("start", {}).get("date"),
                    "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
                })

        return filtered_events

    except HttpError as error:
        print("Google Calendar API Error:", error)
        return []

    except Exception as e:
        print("Unexpected error:", str(e))
        return []


@tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send out an email with the given subject and HTML body """
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("osiemomaina85@gmail.com") # Change this to your verified email
    to_email = To("mainanorbert90@gmail.com") # Change this to your email
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    sg.client.mail.send.post(request_body=mail)
    return "success"



