from agents import Agent
from .guardrails import validate_confirmed_output, validate_scheduler_request
from .schemas import ConfirmedMeeting, InviteDelivery, MeetingRequest, SlotSuggestion
from .tools import confirm_slot, find_common_slots, send_calendar_invite_email

request_parser_agent = Agent(
    name="Meeting Request Parser",
    instructions="""
    Convert the user's meeting request into structured data.
    Extract the topic, participants, preferred_date, duration_minutes, preferences, timezone, and send_invites.
    Set send_invites to true only when the user explicitly approved sending invites.
    Use Africa/Lagos if no timezone is given.
    Keep preferences short and actionable.
    """,
    model="gpt-4o-mini",
    output_type=MeetingRequest,
    input_guardrails=[validate_scheduler_request],
)

slot_suggester_agent = Agent(
    name="Slot Suggester",
    instructions="""
    You are a meeting scheduler.
    Use the find_common_slots tool exactly once.
    Return the best candidate slots sorted from strongest fit to weakest fit.
    Never invent availability.
    """,
    model="gpt-4o-mini",
    tools=[find_common_slots],
    output_type=SlotSuggestion,
)

meeting_confirmer_agent = Agent(
    name="Meeting Confirmer",
    instructions="""
    You will receive the original request plus candidate meeting slots.
    Choose the best slot from candidate_slots.
    Call confirm_slot exactly once for the selected slot.
    Return only the structured confirmed meeting.
    """,
    model="gpt-4o-mini",
    tools=[confirm_slot],
    output_type=ConfirmedMeeting,
    output_guardrails=[validate_confirmed_output],
    handoff_description="Finalize the best slot and return confirmed meeting details.",
)

meeting_coordinator_agent = Agent(
    name="Meeting Coordinator",
    instructions="""
    You are coordinating the last step of scheduling.
    Immediately hand off to the Meeting Confirmer so it can choose the best slot and confirm it.
    Do not summarize or rewrite the payload yourself.
    """,
    model="gpt-4o-mini",
    handoffs=[meeting_confirmer_agent],
)

invite_sender_agent = Agent(
    name="Invite Sender",
    instructions="""
    You send calendar invites for confirmed meetings.
    Use the send_calendar_invite_email tool exactly once.
    Write a clear professional subject line and a concise HTML email body.
    Mention the meeting topic, start time, end time, timezone, and a short reason for the meeting.
    Return only the structured invite delivery result.
    """,
    model="gpt-4o-mini",
    tools=[send_calendar_invite_email],
    output_type=InviteDelivery,
)
