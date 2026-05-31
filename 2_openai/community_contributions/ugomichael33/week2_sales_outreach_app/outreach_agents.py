from agents import (
    Agent,
    Runner,
    GuardrailFunctionOutput,
    input_guardrail,
)

from config import MODEL
from models import (
    ClarifyingQuestions,
    DraftScore,
    EmailDraft,
    FollowUpSequence,
    GuardrailDecision,
    HtmlEmail,
    SendPayload,
)
from tools import lookup_company, send_email


_guardrail_agent = Agent(
    name="Outreach Guardrail",
    instructions=(
        "Decide if the request is appropriate for cold outreach. "
        "Block requests that include harassment, deception, impersonation, bulk/spam outreach, "
        "illegal activity, or scraping personal data. "
        "Return allowed=false with a clear reason and a safe alternative if blocked."
    ),
    output_type=GuardrailDecision,
    model=MODEL,
)


@input_guardrail
async def guardrail_request(ctx, agent, message):
    result = await Runner.run(_guardrail_agent, message, context=ctx.context)
    decision = result.final_output
    return GuardrailFunctionOutput(
        output_info={"reason": decision.reason},
        tripwire_triggered=not decision.allowed,
    )


clarifier_agent = Agent(
    name="Clarifier",
    instructions=(
        "Ask 2-3 clarifying questions to tailor the outreach. "
        "Focus on target role, pain points, and desired CTA."
    ),
    output_type=ClarifyingQuestions,
    model=MODEL,
)

research_agent = Agent(
    name="Lead Researcher",
    instructions=(
        "Given a company name, produce context for sales outreach. "
        "Use lookup_company to fetch structured lead context."
    ),
    tools=[lookup_company],
    model=MODEL,
)

writer_professional = Agent(
    name="Email Writer (Professional)",
    instructions=(
        "Write a concise, professional cold email using the lead context. "
        "Keep it specific and under 120 words."
    ),
    output_type=EmailDraft,
    model=MODEL,
)

writer_concise = Agent(
    name="Email Writer (Concise)",
    instructions=(
        "Write a very concise cold email (under 80 words). "
        "Make the value prop obvious and include a crisp CTA."
    ),
    output_type=EmailDraft,
    model=MODEL,
)

writer_bold = Agent(
    name="Email Writer (Bold)",
    instructions=(
        "Write a bold, punchy cold email that is still professional. "
        "Use a strong opener and a direct CTA."
    ),
    output_type=EmailDraft,
    model=MODEL,
)

scorer_agent = Agent(
    name="Email Evaluator",
    instructions=(
        "Score the email draft (1-10). Favor clarity, relevance, and a crisp CTA."
    ),
    output_type=DraftScore,
    model=MODEL,
)

followup_agent = Agent(
    name="Follow-up Sequencer",
    instructions=(
        "Generate 2-3 follow-up emails based on the winning draft. "
        "Each follow-up should be under 80 words and not repeat the original wording."
    ),
    output_type=FollowUpSequence,
    model=MODEL,
)

formatter_agent = Agent(
    name="HTML Formatter",
    instructions=(
        "Convert the email into clean HTML with a simple layout and clear CTA. "
        "Return both HTML and text versions."
    ),
    output_type=HtmlEmail,
    model=MODEL,
)

send_payload_agent = Agent(
    name="Send Payload Builder",
    instructions=(
        "Create the final send payload using the formatted email. "
        "Fill to_email using RECIPIENT_EMAIL from context if missing."
    ),
    output_type=SendPayload,
    model=MODEL,
)

email_manager = Agent(
    name="Email Manager",
    instructions=(
        "Send the provided email using send_email. "
        "If no recipient is provided, the tool will use RECIPIENT_EMAIL from env. "
        "Do not edit the content."
    ),
    tools=[send_email],
    model=MODEL,
    handoff_description="Send the final email",
)
