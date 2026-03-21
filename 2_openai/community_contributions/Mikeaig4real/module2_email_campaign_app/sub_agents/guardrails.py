"""Guardrails for the email campaign workflow."""

from agents import Agent, input_guardrail, output_guardrail, Runner, GuardrailFunctionOutput
from .models import model_registry
from .schemas import NameCheckOutput, SafetyReviewOutput


name_guardrail_agent = Agent(
    name="name_guardrail",
    instructions=(
        "Check if the input asks to include a personal person name or direct private identifier. "
        "Set is_name_in_message=True when personal naming is requested."
    ),
    output_type=NameCheckOutput,
    model=model_registry["gemini"],
)


output_guardrail_agent = Agent(
    name="output_guardrail",
    instructions=(
        "Review proposed outbound email content. Block if it contains deceptive claims, "
        "fabricated guarantees, or requests for sensitive credentials."
    ),
    output_type=SafetyReviewOutput,
    model=model_registry["gemini"],
)


@input_guardrail
async def guardrail_against_personal_name(ctx, agent, user_input):
    """Block requests that include personal naming."""
    result = await Runner.run(name_guardrail_agent, user_input, context=ctx.context)
    name_check = result.final_output.model_dump()
    blocked = result.final_output.is_name_in_message
    return GuardrailFunctionOutput(
        output_info={"name_check": name_check},
        tripwire_triggered=blocked,
    )


@output_guardrail
async def outbound_safety_guardrail(ctx, agent, output):
    """Block unsafe outbound email content."""
    review = await Runner.run(output_guardrail_agent, str(output), context=ctx.context)
    safety_review = review.final_output.model_dump()
    
    blocked = review.final_output.blocked
    return GuardrailFunctionOutput(
        output_info={"safety_review": safety_review},
        tripwire_triggered=blocked,
    )