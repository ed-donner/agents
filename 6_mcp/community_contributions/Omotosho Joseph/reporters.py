import asyncio
import json
import os
import secrets
import string
from contextlib import AsyncExitStack
from datetime import datetime

import mcp as mcp_lib
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from dotenv import load_dotenv
from agents import (
    Agent,
    Tool,
    Runner,
    trace,
    FunctionTool,
    TracingProcessor,
    Trace,
    Span,
    add_trace_processor,
)
from agents.mcp import MCPServerStdio
from briefing_database import write_log

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# MCP server parameters (from briefing_params.py)
# ---------------------------------------------------------------------------

serper_env = {"SERPER_API_KEY": os.getenv("SERPER_API_KEY")}

briefing_mcp_server_params = [
    {"command": "uv", "args": ["run", "briefing_server.py"]},
]


def researcher_mcp_server_params(name: str):
    return [
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        {
            "command": "npx",
            "args": ["-y", "serper-search-scrape-mcp-server"],
            "env": serper_env,
        },
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},
        },
    ]


# ---------------------------------------------------------------------------
# MCP client helpers (from briefing_client.py)
# ---------------------------------------------------------------------------

_client_params = StdioServerParameters(
    command="uv", args=["run", "briefing_server.py"], env=None
)


async def list_briefing_tools():
    async with stdio_client(_client_params) as streams:
        async with mcp_lib.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools


async def call_briefing_tool(tool_name, tool_args):
    async with stdio_client(_client_params) as streams:
        async with mcp_lib.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return result


async def read_todays_briefing(reporter: str) -> str:
    async with stdio_client(_client_params) as streams:
        async with mcp_lib.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(
                f"briefings://today/{reporter}"
            )
            return result.contents[0].text


async def read_beat_resource(reporter: str) -> str:
    async with stdio_client(_client_params) as streams:
        async with mcp_lib.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(
                f"briefings://beat/{reporter}"
            )
            return result.contents[0].text


async def get_briefing_tools_openai():
    openai_tools = []
    for tool in await list_briefing_tools():
        schema = {**tool.inputSchema, "additionalProperties": False}
        openai_tool = FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=schema,
            on_invoke_tool=lambda ctx, args, toolname=tool.name: call_briefing_tool(
                toolname, json.loads(args)
            ),
        )
        openai_tools.append(openai_tool)
    return openai_tools


# ---------------------------------------------------------------------------
# Prompt templates (from briefing_templates.py)
# ---------------------------------------------------------------------------


def researcher_instructions():
    return f"""You are a news researcher and fact-checker. You search the web for current news, \
verify claims by cross-referencing multiple sources, and produce accurate summaries.

Based on the research request, carry out multiple searches to get comprehensive coverage.
If one source seems unreliable, cross-check with another.
If the web search tool raises an error due to rate limits, use your fetch tool instead.

Make use of your knowledge graph tools to store and recall information about topics, sources, \
and stories you've investigated. Use it to build expertise over time and avoid duplicating work.

The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


def research_tool_description():
    return (
        "This tool researches the web for current news and information. "
        "Describe the topic or story you want investigated. "
        "It will search multiple sources and return a factual summary."
    )


def reporter_instructions(name: str):
    return f"""You are {name}, a journalist who files concise, accurate news briefings.
Your articles should be factual, well-sourced, and relevant to your beat.
You have access to a researcher tool for investigating stories and verifying facts.
You have tools to save articles to the briefing database under your name, {name}.
You can use your entity tools as persistent memory to store and recall information; \
you share this memory with other reporters and can benefit from the group's knowledge.

Your workflow:
1. Use the researcher tool to find the latest news relevant to your beat
2. Select the 2-3 most newsworthy stories
3. For each story, use save_article with your name "{name}", a clear headline, concise summary, and sources
4. After filing, respond with a brief summary of what you covered

Do not fabricate stories. Every article must be grounded in research.
"""


def briefing_message(name: str, beat_description: str, previous_articles: str):
    return f"""Time for your briefing cycle. Research the latest news for your beat and file articles.

Your beat:
{beat_description}

Your recent articles (avoid repeating these topics unless there are significant updates):
{previous_articles}

Current datetime: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Instructions:
1. Use your researcher tool to find 2-3 current, newsworthy stories in your beat
2. For each story, use save_article to file it with your name "{name}", a headline, summary, and sources
3. Use your memory tools to note what you've covered today
4. Respond with a brief 2-3 sentence summary of the stories you filed
"""


# ---------------------------------------------------------------------------
# Tracing (from briefing_tracers.py)
# ---------------------------------------------------------------------------

ALPHANUM = string.ascii_lowercase + string.digits


def make_trace_id(tag: str) -> str:
    tag += "0"
    pad_len = 32 - len(tag)
    random_suffix = "".join(secrets.choice(ALPHANUM) for _ in range(pad_len))
    return f"trace_{tag}{random_suffix}"


class BriefingTracer(TracingProcessor):

    def get_name(self, trace_or_span: Trace | Span) -> str | None:
        trace_id = trace_or_span.trace_id
        name = trace_id.split("_")[1]
        if "0" in name:
            return name.split("0")[0]
        return None

    def on_trace_start(self, trace) -> None:
        name = self.get_name(trace)
        if name:
            write_log(name, "trace", f"Started: {trace.name}")

    def on_trace_end(self, trace) -> None:
        name = self.get_name(trace)
        if name:
            write_log(name, "trace", f"Ended: {trace.name}")

    def on_span_start(self, span) -> None:
        name = self.get_name(span)
        span_type = span.span_data.type if span.span_data else "span"
        if name:
            message = "Started"
            if span.span_data:
                if span.span_data.type:
                    message += f" {span.span_data.type}"
                if hasattr(span.span_data, "name") and span.span_data.name:
                    message += f" {span.span_data.name}"
            write_log(name, span_type, message)

    def on_span_end(self, span) -> None:
        name = self.get_name(span)
        span_type = span.span_data.type if span.span_data else "span"
        if name:
            message = "Ended"
            if span.span_data:
                if span.span_data.type:
                    message += f" {span.span_data.type}"
                if hasattr(span.span_data, "name") and span.span_data.name:
                    message += f" {span.span_data.name}"
                if hasattr(span.span_data, "server") and span.span_data.server:
                    message += f" {span.span_data.server}"
            if span.error:
                message += f" {span.error}"
            write_log(name, span_type, message)

    def force_flush(self) -> None:
        pass

    def shutdown(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Reporter agent (original reporters.py)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Briefing floor — concurrent execution loop (from briefing_floor.py)
# ---------------------------------------------------------------------------

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))

_floor_names = ["Ada", "Marcus", "Zara"]
_floor_model_names = ["gpt-4o-mini"] * 3


def create_reporters():
    return [
        Reporter(name, model_name)
        for name, model_name in zip(_floor_names, _floor_model_names)
    ]


async def run_briefing_cycle():
    add_trace_processor(BriefingTracer())
    reporters = create_reporters()
    while True:
        print("Starting briefing cycle...")
        await asyncio.gather(*[reporter.run() for reporter in reporters])
        print(
            f"Cycle complete. Next run in {RUN_EVERY_N_MINUTES} minutes."
        )
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(
        f"Starting briefing floor — running every "
        f"{RUN_EVERY_N_MINUTES} minutes"
    )
    asyncio.run(run_briefing_cycle())
