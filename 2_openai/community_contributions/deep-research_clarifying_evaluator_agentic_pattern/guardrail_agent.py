from agents import Agent, input_guardrail, Runner, GuardrailFunctionOutput
from pydantic import BaseModel
import asyncio

class AbuseCheckOutput(BaseModel):
    is_abusive_language_used: bool
    abusive_terms: list[str]

INSTRUCTIONS = (
  "Check if user has provided some abusive query input."
  "Check if any sort of sexual context has been provided by the user"
)

guardrail_agent = Agent( 
    name="Abuse check",
    instructions=INSTRUCTIONS,
    output_type=AbuseCheckOutput,
    model="gpt-4o-mini"
)

@input_guardrail
async def guardrail_against_abuse(ctx, agent, message):
    result = await Runner.run(guardrail_agent, message, context=ctx.context)
    is_abusive_language_used = result.final_output.is_abusive_language_used
    return GuardrailFunctionOutput(output_info={"found_abusive_language": result.final_output},tripwire_triggered=is_abusive_language_used)

# class NameCheckOutput(BaseModel):
#     is_name_in_message: bool
#     name: str

# guardrail_agent_2 = Agent( 
#     name="Name check",
#     instructions="Check if the user is including someone's personal name in what they want you to do.",
#     output_type=NameCheckOutput,
#     model="gpt-4o-mini"
# )

# @input_guardrail
# async def guardrail_against_name(ctx, agent, message):
#     result = await Runner.run(guardrail_agent, message, context=ctx.context)
#     is_name_in_message = result.final_output.is_name_in_message
#     return GuardrailFunctionOutput(output_info={"found_name": result.final_output},tripwire_triggered=is_name_in_message)