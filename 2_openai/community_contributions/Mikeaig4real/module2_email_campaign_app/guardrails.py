"""Guardrails for the email campaign workflow."""

from agents import Agent, input_guardrail, output_guardrail, Runner, GuardrailFunctionOutput

from models import model_registry
from schemas import NameCheckOutput, SafetyReviewOutput
from debug import debug_print


name_guardrail_agent = Agent(
    name="name_guardrail",
    instructions=(
        "Check if the input asks to include a personal person name or direct private identifier. "
        "Set is_name_in_message=True ONLY when a specific personal first/last name is requested. "
        "Professional roles, job titles, or departments (e.g., 'CTO', 'Head of Engineering', 'Startup CTO') "
        "are NOT personal names and should NOT be blocked."
    ),
    output_type=NameCheckOutput,
    model=model_registry["openai"]
)


output_guardrail_agent = Agent(
    name="output_guardrail",
    instructions=(
        "You are a Safety Auditor. Review the human-readable text of the proposed email. "
        "IGNORE technical formatting, JSON structures, or debug logs. "
        "ONLY block if the actual email body contains: "
        "1. Deceptive marketing claims (e.g., '100% guaranteed SOC2 in 1 day'). "
        "2. Requests for sensitive passwords or credentials. "
        "3. Explicitly harmful or offensive content. "
        "If the text is a technical summary or a standard business email, ALLOW it."
    ),
    output_type=SafetyReviewOutput,
    model=model_registry["openai"]
)


@input_guardrail
async def guardrail_against_personal_name(ctx, _agent, user_input):
    """Block requests that include personal naming."""
    debug_print(f"DEBUG: guardrail_against_personal_name checking input: '{user_input}'")
    result = await Runner.run(name_guardrail_agent, user_input, context=ctx.context)
    name_check = result.final_output.model_dump()
    blocked = result.final_output.is_name_in_message
    debug_print(f"DEBUG: name_guardrail_agent result: blocked={blocked}, name_found='{result.final_output.name}'")
    return GuardrailFunctionOutput(
        output_info={"name_check": name_check},
        tripwire_triggered=blocked,
    )


@output_guardrail
async def outbound_safety_guardrail(ctx, _agent, output):
    """Block unsafe outbound email content."""
    debug_print("DEBUG: outbound_safety_guardrail checking generated output...")
    review = await Runner.run(output_guardrail_agent, str(output), context=ctx.context)
    safety_review = review.final_output.model_dump()
    
    blocked = review.final_output.blocked
    debug_print(f"DEBUG: outbound_safety_guardrail result: blocked={blocked}, reason='{review.final_output.reason}'")
    return GuardrailFunctionOutput(
        output_info={"safety_review": safety_review},
        tripwire_triggered=blocked,
    )