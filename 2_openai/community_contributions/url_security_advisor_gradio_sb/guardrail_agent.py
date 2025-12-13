from pydantic import BaseModel

from agents import Agent, Runner, input_guardrail, GuardrailFunctionOutput

class DataCheck(BaseModel):
    is_url: bool
    is_email: bool

guardrail_instructions = """
Check if the provided email and url are valid in terms of structure 
Email has @ symbol etc.
Url is absolute has domain etc.
"""

@input_guardrail
async def guardrail_against_data(ctx, agent, message):
    result = await Runner.run(guardrail_agent, message, context=ctx.context)
    is_email = result.final_output.is_email
    is_url = result.final_output.is_url
    return GuardrailFunctionOutput(
        output_info={"is_email": is_email, "is_url": is_url},
        tripwire_triggered=not (is_email and is_url)  
    )

guardrail_agent = Agent( 
    name="Email check",
    instructions=guardrail_instructions,
    output_type=DataCheck,
    model="gpt-4o-mini"
)
