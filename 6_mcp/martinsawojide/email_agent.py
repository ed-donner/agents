from agents import Agent

from model_config import gpt_4o_mini_model

EMAIL_INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the
report converted into clean, well presented HTML with an appropriate subject line."""


def build_email_agent(mcp_servers: list) -> Agent:
    return Agent(
        name="Email agent",
        instructions=EMAIL_INSTRUCTIONS,
        tools=[],
        mcp_servers=mcp_servers,
        model=gpt_4o_mini_model,
    )
