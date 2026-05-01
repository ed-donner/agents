import asyncio

from autogen_agentchat.ui import Console

from showdown import build_football_debate_team


async def main():
    football_team = build_football_debate_team()

    task = "Debate who has had a more impressive season so far in 2026: Chelsea or Manchester City?"

    print("*** Starting Warm Up+ - The dedicated football talk show ***")
    await Console(football_team.run_stream(task=task))


if __name__ == "__main__":
    asyncio.run(main())
