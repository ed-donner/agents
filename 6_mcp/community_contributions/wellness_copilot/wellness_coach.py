from __future__ import annotations

import os
from contextlib import AsyncExitStack

from agents import Agent, Runner, Tool, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

from wellness_mcp_params import coach_mcp_server_params, librarian_mcp_server_params
from wellness_store import log_coach_run
from wellness_templates import coach_instructions, coach_task_message, librarian_instructions

load_dotenv(override=True)

DEFAULT_MODEL = os.getenv("WELLNESS_MODEL", "gpt-4o-mini")
MAX_TURNS = 25


async def _librarian_tool(mcp_servers: list) -> Tool:
    librarian = Agent(
        name="PsychoeducationLibrarian",
        instructions=librarian_instructions(),
        model=DEFAULT_MODEL,
        mcp_servers=mcp_servers,
    )
    return librarian.as_tool(
        tool_name="PsychoeducationLibrarian",
        tool_description=(
            "Use for summaries of trusted psychoeducation from allowlisted public sites (NIMH, NHS, WHO, APA, MHA). "
            "Pass the topic or question; do not use for crisis intervention."
        ),
    )


class WellnessCoach:
    def __init__(self, user_id: str):
        self.user_id = user_id.strip().lower()

    async def run(self, user_message: str) -> str:
        coach_params = coach_mcp_server_params(self.user_id)
        lib_params = librarian_mcp_server_params()
        async with AsyncExitStack() as stack:
            coach_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(p, client_session_timeout_seconds=120)
                )
                for p in coach_params
            ]
            lib_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(p, client_session_timeout_seconds=120)
                )
                for p in lib_params
            ]
            researcher_tool = await _librarian_tool(lib_servers)
            agent = Agent(
                name="WellnessCoach",
                instructions=coach_instructions(self.user_id),
                model=DEFAULT_MODEL,
                tools=[researcher_tool],
                mcp_servers=coach_servers,
            )
            msg = coach_task_message(user_message, self.user_id)
            with trace("wellness_coach"):
                result = await Runner.run(agent, msg, max_turns=MAX_TURNS)
            output = result.final_output or ""
        log_coach_run(self.user_id, output[:8000], {"max_turns": MAX_TURNS})
        return output
