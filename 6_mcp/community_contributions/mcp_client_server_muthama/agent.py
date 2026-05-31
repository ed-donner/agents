import os
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio


load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DEFAULT_MODEL = "gpt-4o-mini"

INSTRUCTIONS = """
You are a friendly and knowledgeable date & time assistant. 
You have access to these MCP tools: current_date, current_time, shift_date(date, days), days_between(date1, date2), weekday_of(date), day_of_week(date), iso_week_number(date), format_date(date, format), to_timestamp(date), from_timestamp(timestamp), and next_weekday(date, weekday).
When a user asks a date/time question:
1. Use the minimal set of tools needed to fetch authoritative values (dates, times, offsets).
2. Combine tool outputs as necessary (e.g., use shift_date or to_timestamp/from_timestamp for arithmetic).
3. Present a short, conversational summary and, when helpful, include exact values or example usage.
Examples: 'Today is 2025-11-12, and the time is 10:00 AM.'
"""


async def run_date_agent(user_query: str, client_session_timeout_seconds: int = 60):
    """
    Run the date/time agent using the Agents SDK-managed MCP server.
    Returns the agent's final output string.
    """
    if "OPENAI_API_KEY" not in os.environ:
        raise RuntimeError("OPENAI_API_KEY must be set in the environment to run the Agent SDK")

    mcp_params = {"command": "uv", "args": ["run", "server.py"]}

    async with MCPServerStdio(params=mcp_params, client_session_timeout_seconds=client_session_timeout_seconds) as mcp_server:
        with trace("date_assistant"):
            agent = Agent(
                name="date_assistant",
                instructions=INSTRUCTIONS,
                model=DEFAULT_MODEL,
                mcp_servers=[mcp_server],
            )
            result = await Runner.run(agent, user_query)
            return result.final_output
