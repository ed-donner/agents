"""Week 6 (MCP) deliverable - an Agents-SDK agent that *consumes* the MCP server.

Spawns accounts_server.py over stdio, hands its tools to an OpenAI Agents-SDK agent, and asks the
agent to trade. The agent auto-discovers the server's tools - no tool wiring on this side. That is
the whole point of MCP: tools live behind a standard protocol, so any MCP-aware agent can use them.

Run: uv run python trader.py     (needs OPENAI_API_KEY)
"""
import asyncio

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv(override=True)


async def main():
    async with MCPServerStdio(
        params={"command": "uv", "args": ["run", "python", "accounts_server.py"]}
    ) as server:                                            # spawn the MCP server as a subprocess
        agent = Agent(
            name="Trader",
            instructions="You manage a trading account using the available tools. Check the balance, "
                         "then buy a sensible position, and report the result.",
            model="gpt-4o-mini",
            mcp_servers=[server],                           # tools discovered automatically
        )
        result = await Runner.run(agent, "Invest about half the cash in tech stocks.")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
