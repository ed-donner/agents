"""Week 6 capstone (MCP) - a mini trading floor: multiple trader agents over multiple MCP servers.

Each trader is an OpenAI Agents-SDK agent that stacks TWO MCP servers (an accounts server and a
market-data server) via AsyncExitStack, looks up prices from the market and records trades through
its own account. The floor runs the traders concurrently with asyncio.gather. The full course
version adds a push server and a Gradio dashboard and runs on a timer; this keeps the architecture
(many servers, many agents, agent-as-tool composition stays one step away) with no paid market feed.

Run: uv run python trading_floor.py     (needs OPENAI_API_KEY)
"""
import asyncio
from contextlib import AsyncExitStack

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv(override=True)

TRADERS = {
    "Warren": "a patient value investor who buys a little of the cheaper solid names",
    "Cathie": "an aggressive growth investor who concentrates on high-upside tech",
}


def server(path):
    return MCPServerStdio(params={"command": "uv", "args": ["run", "python", path]})


async def trade(name, style):
    async with AsyncExitStack() as stack:                       # stack the two MCP servers
        accounts = await stack.enter_async_context(server("accounts_server.py"))
        market = await stack.enter_async_context(server("market_server.py"))
        agent = Agent(
            name=name,
            instructions=(f"You are {name}, {style}. Manage a trading account. Check your balance, "
                          "look up prices from the market, buy a sensible position or two, then "
                          "report your final cash and holdings."),
            model="gpt-4o-mini",
            mcp_servers=[accounts, market],                     # tools from BOTH servers, auto-discovered
        )
        result = await Runner.run(agent, "Do one trading round now.", max_turns=15)
        return name, result.final_output


async def main():
    results = await asyncio.gather(*[trade(name, style) for name, style in TRADERS.items()])
    for name, out in results:
        print(f"\n===== {name} =====\n{out}")


if __name__ == "__main__":
    asyncio.run(main())
