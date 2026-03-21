"""Converged lead agent for email campaign flow."""

from agents import Agent


from sub_agents.concise_sales_agent import concise_sales_agent
from sub_agents.engaging_sales_agent import engaging_sales_agent
from sub_agents.playful_sales_agent import playful_sales_agent
from sub_agents.serious_sales_agent import serious_sales_agent

from sub_agents.guardrails import (
    guardrail_against_personal_name,
    outbound_safety_guardrail,
)

from sub_agents.models import model_registry

from sub_agents.tools import (
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

Steps:
1. Use all available sales agent tools to produce candidate drafts.
2. Choose one final draft with the best relevance and clarity.
3. Pull contacts using get_target_contacts.
4. Build recipient payloads with build_mail_merge_plan.
5. Execute send_mail_merge_dry_run.

Rules:
- Do not invent recipient data.
- Do not send directly; use dry run sender only.
- Return a short summary of why the chosen draft won.
""".strip()

manager_tools = [*sales_tools, get_target_contacts, build_mail_merge_plan, send_mail_merge_dry_run]

sales_manager = Agent(
    name="sales_manager",
    instructions=sales_manager_instructions,
    tools=manager_tools,
    model=model_registry["gemini"],
    input_guardrails=[guardrail_against_personal_name],
    output_guardrails=[outbound_safety_guardrail],
)
