import asyncio
import gradio as gr
from .config import EXAMPLE_REQUESTS
from .schemas import ConfirmedMeeting, InviteDelivery, SlotSuggestion
from .workflow import run_meeting_scheduler

APP_CSS = """
.simple-card {border: 1px solid #d9d9d9; border-radius: 10px; padding: 14px;}
.simple-card h3 {margin: 0 0 10px 0;}
.simple-card p {margin: 6px 0;}
"""


def build_slot_rows(slot_suggestion: SlotSuggestion) -> list[list[str | int]]:
    return [[slot.start, slot.end, slot.score, slot.reason] for slot in slot_suggestion.candidate_slots]


def render_meeting_card(confirmed_meeting: ConfirmedMeeting) -> str:
    participants = "<br>".join(confirmed_meeting.participants)
    return f"""
    <div class='simple-card'>
      <h3>Confirmed Meeting</h3>
      <p><strong>Topic:</strong> {confirmed_meeting.topic}</p>
      <p><strong>When:</strong> {confirmed_meeting.start} to {confirmed_meeting.end} ({confirmed_meeting.timezone})</p>
      <p><strong>Status:</strong> {confirmed_meeting.status}</p>
      <p><strong>Why this slot:</strong> {confirmed_meeting.notes}</p>
      <p><strong>Participants:</strong><br>{participants}</p>
    </div>
    """


def render_notes_card(slot_suggestion: SlotSuggestion) -> str:
    return f"""
    <div class='simple-card'>
      <h3>Scheduling Notes</h3>
      <p>{slot_suggestion.scheduling_notes}</p>
    </div>
    """


def render_invite_card(
    status: str = "waiting",
    headline: str = "Invite Status",
    message: str = "Invites will appear here after scheduling.",
) -> str:
    return f"""
    <div class='simple-card'>
      <h3>{headline}</h3>
      <p><strong>Status:</strong> {status}</p>
      <p>{message}</p>
    </div>
    """


EMPTY_SLOTS = []
EMPTY_MEETING_CARD = render_invite_card("waiting", "No Meeting Yet", "Submit a meeting request to see the recommended schedule.")
EMPTY_NOTES_CARD = render_invite_card("waiting", "No Suggestions Yet", "Candidate time slots will appear here after the scheduler runs.")
EMPTY_INVITE_CARD = render_invite_card()


def format_scheduler_reply(
    confirmed_meeting: ConfirmedMeeting, slot_suggestion: SlotSuggestion, invite_delivery: InviteDelivery
) -> str:
    return (
        f"I found {len(slot_suggestion.candidate_slots)} matching slot(s) and confirmed the strongest option: "
        f"{confirmed_meeting.start} to {confirmed_meeting.end} ({confirmed_meeting.timezone}) for "
        f"'{confirmed_meeting.topic}'. Invite delivery status: {invite_delivery.status}."
    )


def schedule_from_chat(message, history):
    try:
        _, slot_suggestion, confirmed_meeting, invite_delivery = asyncio.run(run_meeting_scheduler(message))
        assistant_message = format_scheduler_reply(confirmed_meeting, slot_suggestion, invite_delivery)
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": assistant_message},
        ]
        return (
            history,
            "",
            build_slot_rows(slot_suggestion),
            render_notes_card(slot_suggestion),
            render_meeting_card(confirmed_meeting),
            render_invite_card(invite_delivery.status, "Calendar Invite", invite_delivery.message),
        )
    except Exception as exc:
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"I couldn't schedule that meeting yet: {exc}"},
        ]
        return history, "", EMPTY_SLOTS, EMPTY_NOTES_CARD, EMPTY_MEETING_CARD, render_invite_card(
            "error", "Scheduling Failed", str(exc)
        )


def build_chat_interface():
    with gr.Blocks(css=APP_CSS) as demo:
        gr.Markdown("# Smart Meeting Scheduler")
        gr.Markdown(
            "Describe the topic, attendees, date, duration, and preferences. If you want invites sent, say so clearly in the request."
        )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Scheduler Chat", type="messages", height=540)
                message = gr.Textbox(
                    label="Meeting Request",
                    placeholder="Schedule a 30-minute launch planning meeting for alice@example.com and bob@example.com on 2026-03-31. Preference: morning. Yes, send the invites after booking.",
                )
                submit = gr.Button("Schedule Meeting", variant="primary")

            with gr.Column(scale=2):
                confirmed_meeting_card = gr.HTML(value=EMPTY_MEETING_CARD)
                scheduling_notes_card = gr.HTML(value=EMPTY_NOTES_CARD)
                suggested_slots_table = gr.Dataframe(
                    headers=["Start", "End"],
                    datatype=["str", "str"],
                    row_count=(0, "dynamic"),
                    col_count=(2, "fixed"),
                    label="Suggested Slots",
                    value=EMPTY_SLOTS,
                    wrap=True,
                    interactive=False,
                )
                invite_status_card = gr.HTML(value=EMPTY_INVITE_CARD)

        gr.Examples(examples=EXAMPLE_REQUESTS, inputs=message)

        schedule_outputs = [
            chatbot,
            message,
            suggested_slots_table,
            scheduling_notes_card,
            confirmed_meeting_card,
            invite_status_card,
        ]

        submit.click(fn=schedule_from_chat, inputs=[message, chatbot], outputs=schedule_outputs)
        message.submit(fn=schedule_from_chat, inputs=[message, chatbot], outputs=schedule_outputs)

    return demo
