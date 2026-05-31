import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from agents import (
    create_goal_analyzer,
    create_scheduler,
    create_optimizer
)


async def main():
    goal_analyzer = create_goal_analyzer()
    scheduler = create_scheduler()
    optimizer = create_optimizer()

    user_input = input("Enter your goals: ")

    # analyze the goals
    msg1 = TextMessage(content=user_input, source="user")
    res1 = await goal_analyzer.on_messages([msg1], cancellation_token=CancellationToken())

    print("\n Tasks:\n", res1.chat_message.content)

    # schedule the tasks
    msg2 = TextMessage(content=res1.chat_message.content, source="goal_analyzer")
    res2 = await scheduler.on_messages([msg2], cancellation_token=CancellationToken())

    print("\n Schedule:\n", res2.chat_message.content)

    # optimize the schedule
    msg3 = TextMessage(content=res2.chat_message.content, source="scheduler")
    res3 = await optimizer.on_messages([msg3], cancellation_token=CancellationToken())

    print("\nFinal To do list:\n", res3.chat_message.content)


if __name__ == "__main__":
    asyncio.run(main())