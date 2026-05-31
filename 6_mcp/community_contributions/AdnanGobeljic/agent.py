import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

load_dotenv(override=True)


async def main():
    params = {"command": "python", "args": ["server.py"]}


    async with MCPServerStdio(params=params) as server:
        agent = Agent(
            name="barista",
            instructions=(
                "You know everything aboutcoffee. Use the tools to answer "
                "questions about beans, roast profiles, brew methods and costs. "
                "Keep answers short and conversational."
            ),
            model="gpt-4o-mini",
            mcp_servers=[server],
        )

        query = input("ask about coffee> ")
        result = await Runner.run(agent, query)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
