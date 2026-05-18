from contextlib import AsyncExitStack
from datetime import datetime
from pathlib import Path
import os


from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from agents import Agent, Runner, OpenAIChatCompletionsModel, trace
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "openai/gpt-4o-mini"
MAX_TURNS = 20

_here = Path(__file__).parent

client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

model = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client)

analyst_mcp_server_params = [
    {"command": "uv", "args": ["run", str(_here / "digest_server.py")]},
]

researcher_mcp_server_params = [
    {"command": "uvx", "args": ["mcp-server-fetch"]},
]


def researcher_instructions():
    return f"""
    You are a legal researcher.
    Fetch web pages and extract policy updates:
    - Laws, regulations, enforcement actions
    - Include jurisdiction and status (proposed, passed, enforced)
    - Focus on factual updates only
    Time: {datetime.now()}
    """


def analyst_instructions(name, beat):
    return f"""
    You are {name}, a policy analyst covering {beat}.

    Write a structured policy digest.
    Use the Researcher tool to fetch sources.

    Save using save_digest.
    """


def analyst_prompt(name, beat, urls):
    return f"""
    You are {name}, covering {beat}.

    Focus URLs:
    {", ".join(urls)}

    Write:

    ## Top Developments
    - 3–5 policy updates with jurisdiction + status

    ## Why It Matters
    - Real-world impact

    ## Risks & Opportunities
    - Business/regulatory risks

    ## What to Watch
    - Upcoming changes

    Time: {datetime.now()}
    """


async def get_researcher_tool(mcp_servers):
    researcher = Agent(
        name="Researcher",
        instructions=researcher_instructions(),
        model=model,
        mcp_servers=mcp_servers,
    )
    return researcher.as_tool(
        tool_name="Researcher",
        tool_description="Fetch and summarize policy updates from URLs",
    )


class Analyst:
    def __init__(self, name, beat, focus_urls):
        self.name = name
        self.beat = beat
        self.focus_urls = focus_urls

    async def run(self):
        try:
            with trace(f"{self.name}-policy"):
                async with AsyncExitStack() as stack:
                    a_servers = [
                        await stack.enter_async_context(
                            MCPServerStdio(p, client_session_timeout_seconds=120)
                        )
                        for p in analyst_mcp_server_params
                    ]

                    r_servers = [
                        await stack.enter_async_context(
                            MCPServerStdio(p, client_session_timeout_seconds=120)
                        )
                        for p in researcher_mcp_server_params
                    ]

                    researcher_tool = await get_researcher_tool(r_servers)

                    agent = Agent(
                        name=self.name,
                        instructions=analyst_instructions(self.name, self.beat),
                        model=model,
                        tools=[researcher_tool],
                        mcp_servers=a_servers,
                    )

                    result = await Runner.run(
                        agent,
                        analyst_prompt(self.name, self.beat, self.focus_urls),
                        max_turns=MAX_TURNS,
                    )

                    return result.final_output
        except Exception as e:
            print(e)
            return None


ANALYSTS = [
    Analyst(
        "US Tech Policy",
        "US regulation",
        [
            "https://www.federalregister.gov",
            "https://www.ftc.gov/news-events",
        ],
    ),
    Analyst(
        "EU Regulation",
        "EU digital policy",
        [
            "https://ec.europa.eu",
            "https://www.europarl.europa.eu",
        ],
    ),
    Analyst(
        "AI Policy",
        "Global AI governance",
        [
            "https://www.oecd.org/ai",
            "https://www.unesco.org/en/artificial-intelligence",
        ],
    ),
]
