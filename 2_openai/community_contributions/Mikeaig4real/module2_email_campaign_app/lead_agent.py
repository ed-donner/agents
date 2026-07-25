"""Converged lead agent for email campaign flow."""

from agents import Agent

from models import model_registry

from sales_agents import (
    concise_sales_agent,
    engaging_sales_agent,
    playful_sales_agent,
    serious_sales_agent,
)

from guardrails import (
    guardrail_against_personal_name,
    outbound_safety_guardrail,
)

from review_agent import review_agent

from tools import (
    build_mail_merge_plan,
    get_target_contacts,
    send_mail_merge_dry_run,
)

sales_tools = [
    concise_sales_agent.as_tool(
        tool_name="concise_sales_agent",
        tool_description="Generate a concise-tone structured cold email.",
    ),
    engaging_sales_agent.as_tool(
        tool_name="engaging_sales_agent",
        tool_description="Generate an engaging-tone structured cold email.",
    ),
    serious_sales_agent.as_tool(
        tool_name="serious_sales_agent",
        tool_description="Generate a serious-tone structured cold email.",
    ),
    playful_sales_agent.as_tool(
        tool_name="playful_sales_agent",
        tool_description="Generate a playful-tone structured cold email.",
    ),
]

sales_manager_instructions = """
You are the Sales Manager.

You MUST follow these 5 steps in EXACT order. Do NOT stop until all steps are complete:
1. Call ALL sales agent tools (concise, engaging, serious, playful) to get candidate drafts.
2. Pass ALL generated drafts to the 'review_agent' 
tool to select the best one and get the justification.
3. Call 'get_target_contacts' to find recipients.
4. Call 'build_mail_merge_plan' using the WINNING draft's subject and content and the contacts.
5. Call 'send_mail_merge_dry_run' with the plan.

Rules:
- DO NOT finish or return a final response until you have called 'send_mail_merge_dry_run'.
- In your final response, YOU MUST include:
  - The full Subject and Body text of the chosen email draft.
  - A brief explanation of why it won.
  - The final report from the dry-run tool.
""".strip()

review_tool = review_agent.as_tool(
    tool_name="review_agent",
    tool_description="""
    Review multiple candidate drafts and select the best one. 
    Pass all candidate drafts as input to this tool.
    """,
)

manager_tools = [
    *sales_tools,
    review_tool,
    get_target_contacts,
    build_mail_merge_plan,
    send_mail_merge_dry_run,
]

sales_manager = Agent(
    name="sales_manager",
    instructions=sales_manager_instructions,
    tools=manager_tools,
    model=model_registry["gemini"],
    input_guardrails=[guardrail_against_personal_name],
    output_guardrails=[outbound_safety_guardrail],
)
