import base64
import os
from datetime import datetime, timedelta
import sendgrid
from agents import function_tool
from sendgrid.helpers.mail import (
    Attachment,
    Content,
    Disposition,
    Email,
    FileContent,
    FileName,
    FileType,
    Mail,
    To,
)
from .config import DEFAULT_TIMEZONE, WORKDAY_END, WORKDAY_START

MOCK_BUSY_CALENDARS = {
    "alice@example.com": {"2026-03-31": [("09:00", "09:30"), ("11:00", "11:30"), ("14:00", "15:00")]},
    "bob@example.com": {"2026-03-31": [("10:00", "10:30"), ("12:00", "13:00"), ("15:30", "16:00")]},
    "carol@example.com": {"2026-03-31": [("09:30", "10:00"), ("13:30", "14:30")]},
    "dave@example.com": {"2026-03-31": [("11:30", "12:00"), ("16:00", "16:30")]},
    "yemigabriel@gmail.com": {"2026-03-31": [("09:00", "10:00"), ("13:00", "13:30")]},
}


def parse_dt(date_str: str, time_str: str) -> datetime:
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")


def overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and start_b < end_a


def score_slot(start: datetime, preferences: list[str]) -> tuple[int, str]:
    preference_text = " ".join(preferences).lower()
    score = 100
    reasons = []

    if "morning" in preference_text and start.hour < 12:
        score += 20
        reasons.append("matches morning preference")
    if "afternoon" in preference_text and start.hour >= 12:
        score += 20
        reasons.append("matches afternoon preference")
    if "earliest" in preference_text:
        score += max(0, 20 - ((start.hour - WORKDAY_START) * 5))
        reasons.append("leans toward the earliest working slot")
    if "avoid lunch" in preference_text or "avoid noon" in preference_text:
        if start.hour == 12:
            score -= 25
        else:
            reasons.append("avoids lunchtime")

    if not reasons:
        reasons.append("works for every participant")

    return score, ", ".join(reasons)


def sender_email() -> str | None:
    return os.environ.get("SENDGRID_FROM_EMAIL") or os.environ.get("FROM_EMAIL") or os.environ.get("EMAIL")


def build_ics_invite(
    topic: str,
    start: str,
    end: str,
    timezone: str,
    description: str,
    organizer: str,
    attendees: list[str],
) -> str:
    start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
    uid = f"{start_dt.strftime('%Y%m%dT%H%M%S')}-{topic.lower().replace(' ', '-')}@meeting-scheduler"
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    attendee_lines = "\n".join([f"ATTENDEE;CN={email};RSVP=TRUE:mailto:{email}" for email in attendees])
    safe_topic = topic.replace(",", " ").replace(";", " ")
    safe_description = description.replace("\n", "\\n").replace(",", " ").replace(";", " ")
    return f"""BEGIN:VCALENDAR
PRODID:-//OpenAI Agents SDK//Smart Meeting Scheduler//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART;TZID={timezone}:{start_dt.strftime('%Y%m%dT%H%M%S')}
DTEND;TZID={timezone}:{end_dt.strftime('%Y%m%dT%H%M%S')}
SUMMARY:{safe_topic}
DESCRIPTION:{safe_description}
ORGANIZER:mailto:{organizer}
{attendee_lines}
END:VEVENT
END:VCALENDAR
"""


@function_tool
def find_common_slots(
    participants: list[str], preferred_date: str, duration_minutes: int, preferences: list[str]
) -> dict:
    """Check mock participant calendars and return mutually available slots."""
    day_start = datetime.strptime(f"{preferred_date} {WORKDAY_START:02d}:00", "%Y-%m-%d %H:%M")
    day_end = datetime.strptime(f"{preferred_date} {WORKDAY_END:02d}:00", "%Y-%m-%d %H:%M")
    duration = timedelta(minutes=duration_minutes)
    candidate_slots = []
    current = day_start

    while current + duration <= day_end:
        slot_end = current + duration
        available_for_all = True

        for participant in participants:
            busy_ranges = MOCK_BUSY_CALENDARS.get(participant, {}).get(preferred_date, [])
            for busy_start, busy_end in busy_ranges:
                if overlaps(current, slot_end, parse_dt(preferred_date, busy_start), parse_dt(preferred_date, busy_end)):
                    available_for_all = False
                    break
            if not available_for_all:
                break

        if available_for_all:
            score, reason = score_slot(current, preferences)
            candidate_slots.append(
                {
                    "start": current.strftime("%Y-%m-%d %H:%M"),
                    "end": slot_end.strftime("%Y-%m-%d %H:%M"),
                    "score": score,
                    "reason": reason,
                }
            )

        current += timedelta(minutes=30)

    candidate_slots.sort(key=lambda slot: (-slot["score"], slot["start"]))
    return {
        "participants": participants,
        "preferred_date": preferred_date,
        "timezone": DEFAULT_TIMEZONE,
        "slots": candidate_slots[:5],
    }


@function_tool
def confirm_slot(topic: str, participants: list[str], start: str, end: str, timezone: str, notes: str) -> dict:
    """Mock-book the selected slot and return confirmed meeting details."""
    return {
        "topic": topic,
        "participants": participants,
        "timezone": timezone,
        "start": start,
        "end": end,
        "status": "confirmed",
        "notes": notes,
    }


@function_tool
def send_calendar_invite_email(
    topic: str,
    participants: list[str],
    start: str,
    end: str,
    timezone: str,
    notes: str,
    subject: str,
    body_html: str,
) -> dict:
    """Send a calendar invite email with an ICS attachment using SendGrid."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_address = sender_email()
    if not api_key:
        return {
            "status": "error",
            "recipients": participants,
            "subject": subject,
            "message": "SENDGRID_API_KEY is not configured.",
        }
    if not from_address:
        return {
            "status": "error",
            "recipients": participants,
            "subject": subject,
            "message": "A verified sender email is missing. Set SENDGRID_FROM_EMAIL, FROM_EMAIL, or EMAIL.",
        }

    ics_text = build_ics_invite(topic, start, end, timezone, notes, from_address, participants)
    encoded_ics = base64.b64encode(ics_text.encode("utf-8")).decode("utf-8")
    sg = sendgrid.SendGridAPIClient(api_key=api_key)

    for participant in participants:
        mail = Mail(Email(from_address), To(participant), subject, Content("text/html", body_html))
        attachment = Attachment()
        attachment.file_content = FileContent(encoded_ics)
        attachment.file_name = FileName("invite.ics")
        attachment.file_type = FileType("text/calendar")
        attachment.disposition = Disposition("attachment")
        mail.attachment = attachment
        sg.client.mail.send.post(request_body=mail.get())

    return {
        "status": "sent",
        "recipients": participants,
        "subject": subject,
        "message": f"Calendar invites were sent to {len(participants)} participant(s).",
    }
