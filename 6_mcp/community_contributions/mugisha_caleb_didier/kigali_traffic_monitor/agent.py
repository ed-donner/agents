from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(override=True)

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from models import TrafficReport
from constants import DEFAULT_MODEL

INSTRUCTIONS = (
    "You are a traffic analyst monitoring road conditions in Kigali, Rwanda. "
    "You have access to a check_all_segments tool that checks all 6 monitored roads at once, "
    "and a get_incidents tool for active incidents.\n"
    "Call check_all_segments once to get traffic data for all roads, "
    "and call get_incidents once to check for any active incidents.\n"
    "The tools already compute congestion_level and delay for you — "
    "use those values directly in your report. "
    "Write a short 2-3 sentence summary that a Kigali commuter would find useful. "
    "Be precise with the numbers — use only what the tools return, do not invent data."
)


async def run_traffic_check() -> TrafficReport:
    """Run a full traffic check across all monitored Kigali road segments."""
    async with MCPServerStdio(
        params={
            "command": "uv",
            "args": ["run", "traffic_server.py"],
        },
        client_session_timeout_seconds=60,
    ) as mcp_server:
        agent = Agent(
            name="kigali_traffic_monitor",
            instructions=INSTRUCTIONS,
            model=DEFAULT_MODEL,
            mcp_servers=[mcp_server],
            output_type=TrafficReport,
        )
        with trace("kigali_traffic_check"):
            result = await Runner.run(
                agent,
                f"Check all Kigali traffic conditions now.\n"
                f"Current UTC time: {datetime.now(timezone.utc).isoformat()}",
                max_turns=10,
            )
            return result.final_output
