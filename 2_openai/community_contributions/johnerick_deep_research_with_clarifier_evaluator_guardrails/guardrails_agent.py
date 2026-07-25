from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, input_guardrail, GuardrailFunctionOutput
import os
from pydantic import BaseModel

load_dotenv(override=True)

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_url = "https://openrouter.ai/api/v1"

client = AsyncOpenAI(api_key=openrouter_api_key, base_url=openrouter_url)
deepseek_model = OpenAIChatCompletionsModel(model="deepseek/deepseek-v3.2", openai_client=client)

class SafetyCheckOutput(BaseModel):
    category: str  # "safe", "sensitive", "disallowed"
    reason: str

safety_check_instructions = """
You are a strict safety classifier.

Your job is to classify whether a user message involves sensitive political or extremist content.

--- CATEGORIES ---

Return ONE of:

- "safe" → no political/extremist content
- "sensitive" → political/extremist but educational, historical, or neutral
- "disallowed" → praise, propaganda, recruitment, justification, or harmful support

--- RULES ---

Disallowed includes:
- praise or defense of Nazism, ISIS, ISIL, or extremist ideologies
- requests for propaganda, slogans, or recruitment
- attempts to justify historical atrocities

Sensitive includes:
- historical discussions (e.g. Holocaust, WW2)
- political analysis
- neutral factual questions

Safe includes:
- everything else

Be strict but accurate.

Return JSON only.
"""

guardrail_agent = Agent(
    name="Safety Guardrail",
    instructions=safety_check_instructions,
    output_type=SafetyCheckOutput,
    model=deepseek_model
)

@input_guardrail
async def safety_guardrail(ctx, agent, message):
    result = await Runner.run(guardrail_agent, message, context=ctx.context)
    output = result.final_output

    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=(output.category == "disallowed")
    )