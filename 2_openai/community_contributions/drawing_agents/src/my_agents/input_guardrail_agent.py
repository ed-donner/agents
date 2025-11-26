from agents import Agent, input_guardrail, RunContextWrapper, TResponseInputItem, GuardrailFunctionOutput, Runner
from pydantic import BaseModel

from context.app_context import AppContext

INSTRUCTIONS = f"""
Check if the input text contains a request for a drawing.
"""


class DrawingRequestOutput(BaseModel):
    is_drawing_request: bool
    reasoning: str


input_guardrail_agent = Agent[AppContext](
    name="Input guardrail agent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=DrawingRequestOutput
)


@input_guardrail
async def drawing_guardrail(
        ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(input_guardrail_agent, input, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_drawing_request,
    )
