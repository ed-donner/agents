from pydantic import BaseModel, Field
from agents import Agent, input_guardrail, GuardrailFunctionOutput, Runner

INSTRUCTIONS = """You are a content moderation agent responsible for reviewing research topics before processing.

Your task is to determine if a research query is appropriate and safe to process.

A research topic is INAPPROPRIATE if it involves:
- Explicit sexual content or pornography
- Illegal activities (drugs, weapons trafficking, fraud, hacking, etc.)
- Violence, harm, or dangerous instructions
- Hate speech, discrimination, or harassment
- Child exploitation or endangerment
- Self-harm or suicide-related content
- Privacy violations or doxxing
- Misinformation intended to cause harm

A research topic is APPROPRIATE if it involves:
- Academic or educational research
- Medical, scientific, or technical topics
- Business, economics, or policy analysis
- Historical or cultural studies
- General information seeking
- Legitimate security research or safety topics

Analyze the query carefully and make a fair judgment. Err on the side of allowing legitimate research while blocking clearly inappropriate content.
"""


class InputGuardrailResult(BaseModel):
    is_appropriate: bool = Field(description="Whether the research topic is appropriate and safe to process")
    reason: str = Field(description="Brief explanation of why the topic was approved or rejected")
    category: str = Field(description="Category of the issue if inappropriate, or 'approved' if appropriate")


content_moderation_agent = Agent(
    name="ContentModerationAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=InputGuardrailResult,
)


@input_guardrail
async def guardrail_research_topic(ctx, agent, query):
    """Check if research topic is appropriate before processing"""
    result = await Runner.run(content_moderation_agent, f"Research topic: {query}", context=ctx.context)
    is_inappropriate = not result.final_output.is_appropriate

    output_info = {
        "is_appropriate": result.final_output.is_appropriate,
        "reason": result.final_output.reason,
        "category": result.final_output.category
    }

    return GuardrailFunctionOutput(
        output_info=output_info,
        tripwire_triggered=is_inappropriate
    )
