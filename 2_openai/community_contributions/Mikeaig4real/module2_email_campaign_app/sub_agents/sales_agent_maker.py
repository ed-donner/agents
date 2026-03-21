"""Sales agent maker module."""

from agents import Agent
from .schemas import ColdEmail

SALES_CONTEXT = """
You work at ComplAI, an AI tool that helps teams prepare for SOC2 audits.
Write outbound emails to B2B prospects. Keep claims realistic and specific.
""".strip()

def make_sales_agent(name: str, tone: str, model):
    """Create one model-specific sales drafter."""
    instructions = f"""
{SALES_CONTEXT}
You write in a {tone} style.
Return output in the schema fields for subject, preview_text, body_text, cta, and tone.
""".strip()
    return Agent(name=name, instructions=instructions, model=model, output_type=ColdEmail)