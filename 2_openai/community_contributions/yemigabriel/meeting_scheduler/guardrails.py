import json
from datetime import datetime
from agents import GuardrailFunctionOutput, input_guardrail, output_guardrail
from .config import WORKDAY_END, WORKDAY_START
from .schemas import ConfirmedMeeting

@input_guardrail
async def validate_scheduler_request(ctx, agent, message):
    text = message if isinstance(message, str) else json.dumps(message)
    lowered = text.lower()
    problems = []

    if "@" not in text:
        problems.append("include at least one participant email")
    if "2026-" not in text and "2025-" not in text and "2027-" not in text:
        problems.append("include a preferred date in YYYY-MM-DD format")
    if "minute" not in lowered:
        problems.append("include the meeting duration in minutes")

    return GuardrailFunctionOutput(output_info={"problems": problems}, tripwire_triggered=bool(problems))


@output_guardrail
async def validate_confirmed_output(ctx, agent, output: ConfirmedMeeting):
    start = datetime.strptime(output.start, "%Y-%m-%d %H:%M")
    end = datetime.strptime(output.end, "%Y-%m-%d %H:%M")
    problems = []

    if end <= start:
        problems.append("end must be later than start")
    if start.hour < WORKDAY_START or end.hour > WORKDAY_END or (end.hour == WORKDAY_END and end.minute > 0):
        problems.append("meeting must stay inside the mock workday")
    if not output.participants:
        problems.append("meeting must include at least one participant")

    return GuardrailFunctionOutput(output_info={"problems": problems}, tripwire_triggered=bool(problems))
