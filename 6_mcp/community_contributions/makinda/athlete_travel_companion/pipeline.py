"""Four specialist agents + sequential pipeline (OpenAI Agents SDK + MCP)."""

from __future__ import annotations

import os
from pathlib import Path

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv(override=True)

SERVER_PATH = Path(__file__).resolve().parent / "athlete_mcp_server.py"

MODEL = os.environ.get("OPENAI_ATHLETE_MODEL", "gpt-4o-mini")

MCP_PARAMS = {
    "command": "uv",
    "args": ["run", "python", str(SERVER_PATH)],
    "env": {**os.environ},
}

PLANNER_INSTRUCTIONS = """
You are the **Planner Agent** for athletes who travel for competition or training camps.

Use the MCP tools you are given:
- **get_training_weather**, **geocode_city**, **get_elevation_meters** to understand heat, wind, rain, and altitude load.
- **list_calendar_events** and **add_calendar_event** for schedule blocks.

Output a single section titled **## Planner** with:
- How today’s environment (weather + elevation vs home) should change session type, volume, and intensity.
- Jet-lag / time-zone considerations if the user mentioned travel.
- Any calendar conflicts or suggested moves (you may propose **add_calendar_event** only if the user asked for scheduling help).
Be specific and conservative; you are not a doctor.
"""

CONNECTOR_INSTRUCTIONS = """
You are the **Connector Agent**. You help athletes find people and places at their destination.

Use:
- **search_places_for_training** for gyms, tracks, studios (pass a clear query and lat/lon if known from context).
- **send_telegram_message** only if the user explicitly asked to send a message or ping someone via Telegram; otherwise draft the text in your reply and say they can approve sending next time.

Output **## Connector** with shortlists of venues and optional intro copy for local groups/coaches.
"""

HEALTH_INSTRUCTIONS = """
You are the **Health Agent**. You do **not** diagnose or treat; you give conservative training-safety guidance.

Consider fatigue, sleep disruption, niggles, and illness signals described by the user or implied by travel.
Use prior sections (Planner, Connector) as context. You have **no tools**—reason only from the text.

Output **## Health** with red/yellow/green style guidance and when to skip or modify training.
"""

LOG_INSTRUCTIONS = """
You are the **Log Agent** for workout and travel notes.

Use:
- **read_recent_workout_log** to see recent sessions.
- **append_workout_log** to record today’s planned or completed work when the user gave enough detail (session type, duration, RPE).

Output **## Log** with a brief summary of what was recorded or what you recommend logging next.
"""


def build_agents(mcp: MCPServerStdio) -> tuple[Agent, Agent, Agent, Agent]:
    common = {"model": MODEL, "mcp_servers": [mcp]}
    planner = Agent(
        name="planner",
        instructions=PLANNER_INSTRUCTIONS.strip(),
        **common,
    )
    connector = Agent(
        name="connector",
        instructions=CONNECTOR_INSTRUCTIONS.strip(),
        **common,
    )
    health = Agent(
        name="health",
        instructions=HEALTH_INSTRUCTIONS.strip(),
        model=MODEL,
    )
    log_agent = Agent(
        name="log",
        instructions=LOG_INSTRUCTIONS.strip(),
        **common,
    )
    return planner, connector, health, log_agent


async def run_pipeline(user_message: str) -> str:
    """Run Planner → Connector → Health → Log with shared context."""
    async with MCPServerStdio(
        params=MCP_PARAMS,
        client_session_timeout_seconds=120,
    ) as mcp:
        planner, connector, health, log_agent = build_agents(mcp)
        ctx = ""

        with trace("athlete_travel_planner"):
            r1 = await Runner.run(
                planner,
                f"User request:\n{user_message}\n\nProduce only your ## Planner section.",
            )
        ctx += r1.final_output + "\n\n"

        with trace("athlete_travel_connector"):
            r2 = await Runner.run(
                connector,
                f"User request:\n{user_message}\n\nContext so far:\n{ctx}\n\nProduce only your ## Connector section.",
            )
        ctx += r2.final_output + "\n\n"

        with trace("athlete_travel_health"):
            r3 = await Runner.run(
                health,
                f"User request:\n{user_message}\n\nContext so far:\n{ctx}\n\nProduce only your ## Health section.",
            )
        ctx += r3.final_output + "\n\n"

        with trace("athlete_travel_log"):
            r4 = await Runner.run(
                log_agent,
                f"User request:\n{user_message}\n\nContext so far:\n{ctx}\n\nProduce only your ## Log section.",
            )

        return "\n\n".join(
            [
                "# Athlete Travel Companion — brief",
                r1.final_output,
                r2.final_output,
                r3.final_output,
                r4.final_output,
            ]
        )
