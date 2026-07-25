import json
from agents import Runner, trace
from .agents import invite_sender_agent, meeting_coordinator_agent, request_parser_agent, slot_suggester_agent
from .schemas import InviteDelivery

async def run_meeting_scheduler(request_text: str):
    with trace("Smart Meeting Scheduler"):
        parsed_request_result = await Runner.run(request_parser_agent, request_text)
        parsed_request = parsed_request_result.final_output

        suggestion_input = json.dumps(parsed_request.model_dump(), indent=2)
        slot_suggestion_result = await Runner.run(slot_suggester_agent, suggestion_input)
        slot_suggestion = slot_suggestion_result.final_output

        confirmation_payload = json.dumps(
            {
                "request": parsed_request.model_dump(),
                "slot_suggestion": slot_suggestion.model_dump(),
            },
            indent=2,
        )
        confirmed_result = await Runner.run(meeting_coordinator_agent, confirmation_payload)
        confirmed_meeting = confirmed_result.final_output

        if parsed_request.send_invites:
            invite_result = await Runner.run(
                invite_sender_agent, json.dumps(confirmed_meeting.model_dump(), indent=2)
            )
            invite_delivery = invite_result.final_output
        else:
            invite_delivery = InviteDelivery(
                status="skipped",
                recipients=confirmed_meeting.participants,
                subject=f"Invite for {confirmed_meeting.topic}",
                message="Invites were not sent because the request did not include explicit approval.",
            )

    return parsed_request, slot_suggestion, confirmed_meeting, invite_delivery
