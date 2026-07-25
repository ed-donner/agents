"""
All sales agents
"""

from agents import Agent

from models import model_registry
from schemas import ColdEmail



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





concise_sales_agent = make_sales_agent("Concise Sales Agent", "concise", model_registry["deepseek"])
engaging_sales_agent = make_sales_agent("Engaging Sales Agent", "engaging", model_registry["anthropic"])
playful_sales_agent = make_sales_agent("Playful Sales Agent", "playful", model_registry["gemini"])
serious_sales_agent = make_sales_agent("Serious Sales Agent", "serious", model_registry["openai"])