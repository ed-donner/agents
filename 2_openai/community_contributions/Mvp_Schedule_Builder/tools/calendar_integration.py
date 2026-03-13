"""
Google Calendar Integration Service

Simple service for creating calendars and events from scheduler agent output.
"""

from datetime import datetime
import logging

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from product_agents.scheduler_agent import Schedule, Activity
from agents import function_tool


# Google Calendar API scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarIntegration:
    """Service class for integrating with Google Calendar API."""

    def __init__(
        self, credentials_file: str = "credentials.json", token_file: str = "token.json"
    ):
        """
        Initialize Google Calendar service.

        Args:
            credentials_file: Path to Google credentials JSON file
            token_file: Path to store/load authentication token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Google Calendar API."""
        creds = None

        # Load existing token
        try:
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        except FileNotFoundError:
            pass

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Try authentication with fixed ports
                ports_to_try = [8080, 8081, 8082]
                auth_successful = False

                for port in ports_to_try:
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_file, SCOPES
                        )
                        # Use fixed port with additional OAuth parameters to prevent CSRF issues
                        creds = flow.run_local_server(
                            port=port,
                            open_browser=True,
                            access_type="offline",
                            include_granted_scopes="true",
                        )
                        auth_successful = True
                        logging.info(f"OAuth authentication successful on port {port}")
                        break
                    except OSError as port_error:
                        if "Address already in use" in str(port_error):
                            logging.warning(f"Port {port} is busy, trying next port...")
                            continue
                        else:
                            raise port_error
                    except Exception as auth_error:
                        if "mismatching_state" in str(auth_error) or "CSRF" in str(
                            auth_error
                        ):
                            logging.error(
                                f"CSRF state mismatch on port {port}. Clearing token and retrying..."
                            )
                            # Remove existing token file to clear state
                            import os

                            if os.path.exists(self.token_file):
                                os.remove(self.token_file)
                                logging.info("Cleared existing token file")
                            continue
                        elif "invalid_request" in str(
                            auth_error
                        ) or "redirect_uri" in str(auth_error):
                            logging.error(
                                f"OAuth redirect URI not registered for port {port}"
                            )
                            continue
                        else:
                            logging.error(
                                f"Authentication error on port {port}: {auth_error}"
                            )
                            continue

            # Save credentials for future use
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)

    def create_calendar(self, calendar_name: str, description: str = "") -> str:
        """
        Create a new Google Calendar.

        Args:
            calendar_name: Name of the calendar to create
            description: Optional calendar description

        Returns:
            Calendar ID of the created calendar
        """
        calendar_body = {
            "summary": calendar_name,
            "description": description,
            "timeZone": "UTC",
        }

        try:
            calendar = self.service.calendars().insert(body=calendar_body).execute()
            calendar_id = calendar["id"]
            logging.info(f"Created calendar: {calendar_name} (ID: {calendar_id})")
            return calendar_id
        except Exception as e:
            logging.error(f"Failed to create calendar {calendar_name}: {e}")
            raise

    def create_event(self, calendar_id: str, activity: Activity) -> str:
        """
        Create a calendar event from an Activity.

        Args:
            calendar_id: Google Calendar ID
            activity: Activity object with event details

        Returns:
            Event ID of the created event
        """
        # Parse dates (assuming YYYY-MM-DD format)
        start_date = self._parse_date(activity.start_date)
        end_date = self._parse_date(activity.end_date)

        event_body = {
            "summary": activity.name,
            "description": activity.description,
            "start": {"date": start_date, "timeZone": "UTC"},
            "end": {"date": end_date, "timeZone": "UTC"},
        }

        try:
            event = (
                self.service.events()
                .insert(calendarId=calendar_id, body=event_body)
                .execute()
            )
            event_id = event["id"]
            logging.info(f"Created event: {activity.name} (ID: {event_id})")
            return event_id
        except Exception as e:
            logging.error(f"Failed to create event {activity.name}: {e}")
            raise

    def sync_schedule(self, schedule: Schedule) -> dict:
        """
        Create a calendar and sync all activities from a Schedule.

        Args:
            schedule: Schedule object containing calendar name and activities

        Returns:
            Dictionary with calendar_id and list of event_ids
        """
        # Create the calendar
        calendar_id = self.create_calendar(
            calendar_name=schedule.calendar_name,
            description=f"Project schedule with {len(schedule.activities)} activities",
        )

        # Create events for all activities
        event_ids = []
        for activity in schedule.activities:
            try:
                event_id = self.create_event(calendar_id, activity)
                event_ids.append(event_id)
            except Exception as e:
                logging.warning(f"Skipped activity {activity.name}: {e}")
                continue

        result = {
            "calendar_id": calendar_id,
            "event_ids": event_ids,
            "total_events": len(event_ids),
            "activities_processed": len(schedule.activities),
        }

        logging.info(
            f"Synced schedule '{schedule.calendar_name}': "
            f"{result['total_events']}/{result['activities_processed']} events created"
        )

        return result

    # Add this method to GoogleCalendarIntegration

    def ensure_authenticated(self) -> bool:
        """Check if already authenticated, return status."""
        try:
            # Try a simple API call to test authentication
            self.service.calendarList().list(maxResults=1).execute()
            return True
        except Exception:
            return False

    def reset_authentication(self) -> None:
        """Reset authentication state by clearing token file."""
        import os

        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            logging.info("Cleared authentication token file")
        self.service = None

    def _parse_date(self, date_str: str) -> str:
        """
        Parse and validate date string.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Validated date string
        """
        try:
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            # Try alternative formats or default to today
            try:
                # Try MM/DD/YYYY format
                parsed = datetime.strptime(date_str, "%m/%d/%Y")
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                logging.warning(f"Invalid date format: {date_str}, using today's date")
                return datetime.now().strftime("%Y-%m-%d")


class CalendarIntegrationError(Exception):
    """Custom exception for calendar integration errors."""

    pass


# Global calendar service instance
_calendar_service = None


def get_calendar_service():
    """Get or create a singleton calendar service instance."""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = GoogleCalendarIntegration()
    return _calendar_service


@function_tool
def sync_schedule_to_calendar(schedule: Schedule) -> dict:
    """
    Create a Google Calendar and sync all activities from a project schedule.

    Args:
        schedule: Schedule object containing calendar name and list of activities

    Returns:
        Dictionary with calendar_id, event_ids, and sync statistics
    """
    try:
        # Get calendar service and sync the schedule directly
        calendar_service = get_calendar_service()

        if not calendar_service.ensure_authenticated():
            return {
                "status": "error",
                "message": "Google Calendar authentication required. Please run authentication setup first.",
            }

        print("Syncing schedule to Google Calendar...")
        result = calendar_service.sync_schedule(schedule)
        print("✅ Successfully synced schedule!")

        return {
            "status": "success",
            "message": f"Successfully synced schedule '{schedule.calendar_name}'",
            "calendar_id": result["calendar_id"],
            "total_events_created": result["total_events"],
            "activities_processed": result["activities_processed"],
            "event_ids": result["event_ids"],
        }

    except Exception as e:
        error_msg = f"Failed to sync schedule to calendar: {str(e)}"
        logging.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "calendar_id": None,
            "total_events_created": 0,
            "activities_processed": 0,
            "event_ids": [],
        }
