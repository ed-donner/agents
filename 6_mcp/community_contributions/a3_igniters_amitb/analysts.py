from contextlib import AsyncExitStack
from datetime import datetime
from pathlib import Path
import os

import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-4o-mini"
MAX_TURNS = 20

_here = Path(__file__).parent

openrouter_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

model = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=openrouter_client)

analyst_mcp_server_params = [
    {"command": "uv", "args": ["run", str(_here / "digest_server.py")]},
]

researcher_mcp_server_params = [
    {"command": "uvx", "args": ["mcp-server-fetch"]},
]

_digest_stdio_params = StdioServerParameters(
    command="uv",
    args=["run", str(_here / "digest_server.py")],
    env=None,
)


async def read_beat_resource(name: str) -> str:
    async with stdio_client(_digest_stdio_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"digests://beat/{name}")
            return result.contents[0].text


async def read_recent_resource(name: str) -> str:
    async with stdio_client(_digest_stdio_params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"digests://recent/{name}")
            return result.contents[0].text


def researcher_instructions() -> str:
    return f"""You are a news researcher. You fetch web pages and extract the most important stories from them.
Given a request with a list of URLs, fetch each page and summarise the key stories you find.
Make multiple fetches for comprehensive coverage, then synthesise your findings into a brief, factual summary.
Focus on facts, key developments, and emerging trends. Ignore ads, navigation, and boilerplate.
The current datetime is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""


def research_tool_description() -> str:
    return (
        "Fetches and summarises the latest news from web pages. "
        "Provide a description of what to look for and the URLs to check."
    )


def analyst_instructions(name: str, beat: str) -> str:
    return f"""You are {name}, a news analyst covering {beat}.
Your job is to survey the latest developments in your beat and write a concise daily digest.
You have a Researcher tool that fetches and summarises web pages for you.
You have tools to retrieve your beat details (get_analyst_beat) and to save/retrieve past digests.
After gathering the news, call save_digest to persist your work, then respond with the complete digest.
"""


def analyst_prompt(name: str, beat: str, focus_urls: list[str]) -> str:
    urls = ", ".join(focus_urls)
    return f"""You are {name}, covering {beat}.
Use get_analyst_beat to confirm your focus sources, then use the Researcher to fetch the latest news from them.
Write a digest with:
- **Top Stories**: 3-5 stories with a brief summary each
- **Trends to Watch**: 2-3 key themes emerging from today's news

Save the digest using save_digest, then respond with the complete digest.
Current datetime: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


async def get_researcher(mcp_servers: list) -> Agent:
    return Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=model,
        mcp_servers=mcp_servers,
    )


async def get_researcher_tool(mcp_servers: list) -> Tool:
    researcher = await get_researcher(mcp_servers)
    return researcher.as_tool(
        tool_name="Researcher",
        tool_description=research_tool_description(),
    )


class Analyst:
    def __init__(self, name: str, beat: str, focus_urls: list[str]):
        self.name = name
        self.beat = beat
        self.focus_urls = focus_urls
        self.agent = None

    async def create_agent(self, analyst_mcp_servers: list, researcher_mcp_servers: list) -> Agent:
        researcher_tool = await get_researcher_tool(researcher_mcp_servers)
        self.agent = Agent(
            name=self.name,
            instructions=analyst_instructions(self.name, self.beat),
            model=model,
            tools=[researcher_tool],
            mcp_servers=analyst_mcp_servers,
        )
        return self.agent

    async def run_agent(self, analyst_mcp_servers: list, researcher_mcp_servers: list) -> str:
        await self.create_agent(analyst_mcp_servers, researcher_mcp_servers)
        prompt = analyst_prompt(self.name, self.beat, self.focus_urls)
        result = await Runner.run(self.agent, prompt, max_turns=MAX_TURNS)
        return result.final_output

    async def run_with_mcp_servers(self) -> str:
        async with AsyncExitStack() as stack:
            a_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in analyst_mcp_server_params
            ]
            async with AsyncExitStack() as stack:
                r_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params
                ]
                return await self.run_agent(a_mcp_servers, r_mcp_servers)

    async def run(self) -> str | None:
        try:
            with trace(f"{self.name}-digest"):
                return await self.run_with_mcp_servers()
        except Exception as e:
            print(f"Error running analyst {self.name}: {e}")
            return None


ANALYSTS = [
    Analyst(
        name="Rahul",
        beat="AI & Technology",
        focus_urls=[
            "https://news.ycombinator.com",
            "https://techcrunch.com/category/artificial-intelligence",
            "https://www.theverge.com/ai-artificial-intelligence",
        ],
    ),
    Analyst(
        name="Ram",
        beat="Climate & Energy",
        focus_urls=[
            "https://www.bbc.com/news/science-environment",
            "https://insideclimatenews.org",
            "https://www.carbonbrief.org",
        ],
    ),
    Analyst(
        name="Ali",
        beat="Health & Biotech",
        focus_urls=[
            "https://www.statnews.com",
            "https://www.biopharmadive.com",
            "https://medicalxpress.com",
        ],
    ),
    Analyst(
        name="Soham",
        beat="Startups & Venture Capital",
        focus_urls=[
            "https://techcrunch.com/category/startups",
            "https://venturebeat.com",
            "https://news.crunchbase.com",
        ],
    ),
]
