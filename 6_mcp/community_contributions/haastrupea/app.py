
from agents.mcp import MCPServerStdio
from agents import Agent, Runner
import asyncio
from model_client import model_client

async def chat_once(user_input: str) -> None:

    params = {"command": "uv", "args": ["run", "accounts_server.py"]}
    instructions = "You are a technical fintech support helping user to manage, and answer questions about the Transactions."

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(name="account_manager", instructions=instructions, model=model_client, mcp_servers=[mcp_server])
        result = await Runner.run(agent, user_input)

    print("\nAssistant:")
    print(result.final_output)
    print(f"\nHandled by: {result.last_agent.name}")


async def main() -> None:
    tests = [
        "What is my balance?",
        "Check TXN-1002",
        "Why did transaction TXN-1003 fail?",
        "Why was I charged for deposit?",
        "What is the fee for transfer?",
    ]

    for prompt in tests:
        print(f"\nUser: {prompt}")
        await chat_once(prompt)


if __name__ == "__main__":
    asyncio.run(main())