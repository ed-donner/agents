from contextlib import AsyncExitStack
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from mcp_params import coach_mcp_server_params
from templates import coach_instructions, coach_prompt


class Coach:
    def __init__(self, cv: str):
        self.cv = cv

    async def run(self, job_url: str):
        async with AsyncExitStack() as stack:
            mcp_servers = [
                await stack.enter_async_context(MCPServerStdio(params, client_session_timeout_seconds=30))
                for params in coach_mcp_server_params
            ]

            agent = Agent(
                name="Coach",
                instructions=coach_instructions(self.cv),
                mcp_servers=mcp_servers,
                model="gpt-4o-mini",
            )

            with trace("Job Application Coach"):
                result = await Runner.run(agent, coach_prompt(job_url), max_turns=20)

        return result.final_output
