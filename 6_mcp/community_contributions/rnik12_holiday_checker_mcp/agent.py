import os
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

load_dotenv(override=True)
DEFAULT_MODEL = "gpt-4o-mini"

INSTRUCTIONS = """
You are a helpful Holiday Checker assistant. You can:
- check_holidays(country, state?, city?, start_date, end_date): list holidays in a date range
- is_holiday(country, date, state?): boolean + holiday name if any
- get calendar via resource holidays://calendar/{country}/{year}

When asked, choose the simplest tool(s). Return a short summary first, then bullet the results.
Use ISO date format YYYY-MM-DD. If the user mentions a city, include it in your summary (informational only).
"""


async def run_holiday_agent(user_query: str, client_session_timeout_seconds: int = 60):
    """
    Run the holiday agent using the Agents SDK-managed MCP server.
    Returns the agent's final output string.
    """
    if "OPENAI_API_KEY" not in os.environ:
        raise RuntimeError(
            "OPENAI_API_KEY must be set in the environment to run the Agent SDK"
        )

    mcp_params = {"command": "uv", "args": ["run", "server.py"]}

    async with MCPServerStdio(
        params=mcp_params, client_session_timeout_seconds=client_session_timeout_seconds
    ) as mcp:
        with trace("holiday_checker"):
            agent = Agent(
                name="holiday_checker",
                instructions=INSTRUCTIONS,
                model=DEFAULT_MODEL,
                mcp_servers=[mcp],
            )
            result = await Runner.run(agent, user_query)
            return result.final_output
