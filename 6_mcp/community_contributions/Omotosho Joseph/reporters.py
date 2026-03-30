from contextlib import AsyncExitStack
from briefing_client import read_todays_briefing, read_beat_resource
from briefing_tracers import make_trace_id
from agents import Agent, Tool, Runner, trace
from agents.mcp import MCPServerStdio
from briefing_templates import (
    researcher_instructions,
    reporter_instructions,
    briefing_message,
    research_tool_description,
)
from briefing_params import briefing_mcp_server_params, researcher_mcp_server_params
from dotenv import load_dotenv
import json

load_dotenv(override=True)

MAX_TURNS = 30


async def get_researcher(mcp_servers, model_name="gpt-4o-mini") -> Agent:
    return Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=model_name,
        mcp_servers=mcp_servers,
    )


async def get_researcher_tool(mcp_servers, model_name="gpt-4o-mini") -> Tool:
    researcher = await get_researcher(mcp_servers, model_name)
    return researcher.as_tool(
        tool_name="Researcher",
        tool_description=research_tool_description(),
    )


class Reporter:
    def __init__(self, name: str, model_name: str = "gpt-4o-mini"):
        self.name = name
        self.model_name = model_name
        self.agent = None

    async def create_agent(
        self, briefing_mcp_servers, researcher_mcp_servers
    ) -> Agent:
        tool = await get_researcher_tool(
            researcher_mcp_servers, self.model_name
        )
        self.agent = Agent(
            name=self.name,
            instructions=reporter_instructions(self.name),
            model=self.model_name,
            tools=[tool],
            mcp_servers=briefing_mcp_servers,
        )
        return self.agent

    async def get_context(self) -> tuple[str, str]:
        beat = await read_beat_resource(self.name)
        articles = await read_todays_briefing(self.name)
        return beat, articles

    async def run_agent(self, briefing_mcp_servers, researcher_mcp_servers):
        self.agent = await self.create_agent(
            briefing_mcp_servers, researcher_mcp_servers
        )
        beat, previous_articles = await self.get_context()
        message = briefing_message(self.name, beat, previous_articles)
        await Runner.run(self.agent, message, max_turns=MAX_TURNS)

    async def run_with_mcp_servers(self):
        async with AsyncExitStack() as stack:
            briefing_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in briefing_mcp_server_params
            ]
            async with AsyncExitStack() as inner_stack:
                researcher_servers = [
                    await inner_stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params(self.name)
                ]
                await self.run_agent(briefing_servers, researcher_servers)

    async def run_with_trace(self):
        trace_name = f"{self.name}-briefing"
        trace_id = make_trace_id(self.name.lower())
        with trace(trace_name, trace_id=trace_id):
            await self.run_with_mcp_servers()

    async def run(self):
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running reporter {self.name}: {e}")
