from typing import Literal
from pydantic import BaseModel, Field

class MeetingRequest(BaseModel):
    topic: str = Field(description="The meeting topic or agenda.")
    participants: list[str] = Field(description="All attendee email addresses.")
    preferred_date: str = Field(description="Preferred meeting date in YYYY-MM-DD format.")
    duration_minutes: int = Field(description="Requested meeting duration in minutes.", gt=0, le=180)
    preferences: list[str] = Field(
        default_factory=list,
        description="Scheduling preferences such as morning, afternoon, earliest, or avoid lunch.",
    )
    timezone: str = Field(default="Africa/Lagos", description="Timezone for the meeting.")
    send_invites: bool = Field(
        default=False,
        description="Whether the user explicitly approved sending calendar invites after scheduling.",
    )

class TimeSlot(BaseModel):
    start: str = Field(description="Slot start in YYYY-MM-DD HH:MM format.")
    end: str = Field(description="Slot end in YYYY-MM-DD HH:MM format.")
    score: int = Field(description="Heuristic ranking score for this slot.")
    reason: str = Field(description="Why this slot is a strong fit.")


class SlotSuggestion(BaseModel):
    topic: str
    participants: list[str]
    timezone: str
    candidate_slots: list[TimeSlot] = Field(
        description="Best available meeting options sorted from best to worst."
    )
    scheduling_notes: str = Field(description="Brief explanation of how the suggestions were chosen.")


class ConfirmedMeeting(BaseModel):
    topic: str
    participants: list[str]
    timezone: str
    start: str
    end: str
    status: Literal["confirmed"]
    notes: str = Field(description="Short explanation of why the meeting was booked into this slot.")


class InviteDelivery(BaseModel):
    status: Literal["sent", "skipped", "error"]
    recipients: list[str]
    subject: str
    message: str
