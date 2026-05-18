from agents import Agent, Runner, trace, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import asyncio
from IPython.display import display, Markdown


load_dotenv(override=True)
openrouter_key = os.getenv("OPENROUTER_API_KEY")
openrouter_client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key)

DEFAULT_MODEL = "openai/gpt-4o-mini"

openrouter_model = OpenAIChatCompletionsModel(model=DEFAULT_MODEL, openai_client=openrouter_client)

INSTRUCTIONS = """
You are a sport research agent. You are given a sport and you need to research the sport and return the information about the sport.
You have access to the following tools:
- get_sport_info: Get information about a sport

Follow these steps:
1. Research the sport
2. Return the information about the sport

If the sport is not found, return "Sport not found"

If the sport is found, return the information about the sport

Return the information about the sport in a markdown format
"""

async def main(sport: str):
    async with MCPServerStdio(params={"command": "uv", "args": ["run", "sport_server.py"]}, client_session_timeout_seconds=60) as mcp_server:
        agent = Agent(
            name="sport_research_agent",
            instructions=INSTRUCTIONS,
            model=openrouter_model,
            mcp_servers=[mcp_server],
        )
        with trace("sport_research_agent"):
            result = await Runner.run(agent, sport)
            display(Markdown(result.final_output))
            print(result.final_output)

if __name__ == "__main__":
    sport = "basketball"
    asyncio.run(main(sport))
