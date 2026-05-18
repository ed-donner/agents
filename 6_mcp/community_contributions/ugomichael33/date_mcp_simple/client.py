import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from config import MODEL


async def main():
    params = {
        "command": "uv",
        "args": ["run", "server.py"],
    }

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(
            name="date_assistant",
            instructions=(
                "You can call MCP tools to get the current date/time. "
                "Use current_date or current_datetime when asked about time."
            ),
            model=MODEL,
            mcp_servers=[mcp_server],
        )

        prompt = "What is the current date and time in UTC?"
        result = await Runner.run(agent, prompt)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
