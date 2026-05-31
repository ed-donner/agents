
from fintech_agents import manager
from agents import Runner
import asyncio

async def chat_once(user_input: str) -> None:
    result = await Runner.run(manager, user_input)
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