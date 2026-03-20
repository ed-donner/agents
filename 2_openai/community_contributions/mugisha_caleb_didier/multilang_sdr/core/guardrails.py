from pydantic import BaseModel
from agents import Agent, Runner, input_guardrail, output_guardrail, GuardrailFunctionOutput


class ProspectCheckOutput(BaseModel):
    is_valid: bool
    reason: str


prospect_check_agent = Agent(
    name="Prospect Checker",
    instructions=(
        "You check whether the user's message contains a valid sales prospect description. "
        "A valid prospect includes at least a company name or role/title of the person being contacted. "
        "Generic greetings like 'hello' or 'hi' or vague messages without any prospect info are invalid. "
        "Return is_valid=True if the message describes a real prospect, False otherwise."
    ),
    output_type=ProspectCheckOutput,
    model="gpt-4o-mini",
)


@input_guardrail
async def validate_prospect_input(ctx, agent, message):
    result = await Runner.run(prospect_check_agent, message, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info={"prospect_check": result.final_output},
        tripwire_triggered=not result.final_output.is_valid,
    )


class CompetitorCheckOutput(BaseModel):
    mentions_competitor: bool
    competitor_found: str


competitor_check_agent = Agent(
    name="Competitor Checker",
    instructions=(
        "You check whether a sales email mentions any competitor products or companies by name. "
        "Common competitors include Salesforce, HubSpot, Outreach, Apollo, SalesLoft, Freshsales, "
        "Pipedrive, ZoomInfo, Gong, and similar sales/CRM tools. "
        "If a competitor is mentioned, set mentions_competitor=True and competitor_found to the name. "
        "If no competitor is mentioned, set mentions_competitor=False and competitor_found to an empty string."
    ),
    output_type=CompetitorCheckOutput,
    model="gpt-4o-mini",
)


@output_guardrail
async def block_competitor_mentions(ctx, agent, output):
    result = await Runner.run(competitor_check_agent, str(output), context=ctx.context)
    return GuardrailFunctionOutput(
        output_info={"competitor_check": result.final_output},
        tripwire_triggered=result.final_output.mentions_competitor,
    )
