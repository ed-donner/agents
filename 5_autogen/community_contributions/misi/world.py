from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost
from creator import Creator
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from autogen_core import AgentId
import messages
import asyncio
from pathlib import Path
import random

HOW_MANY_AGENTS = 10
CHANCES_THAT_I_CHANGE_CREATOR = 0.5
BASE_DIR = Path(__file__).resolve().parent


async def create_next_creator(worker, creator_id, creator_number: int) -> AgentId:
    creator_name = f"creator{creator_number}"
    try:
        creator_result = await worker.send_message(
            messages.Message(content=f"{creator_name}.py"), creator_id
        )
        with open(BASE_DIR / f"{creator_name}.md", "w", encoding="utf-8") as f:
            f.write(creator_result.content)
        print(f"Switching future agent creation to {creator_name}")
        return AgentId(creator_name, "default")
    except Exception as e:
        print(f"Failed to create creator replica {creator_name} due to exception: {e}")
        return creator_id


async def create_and_message(worker, creator_id, i: int) -> bool:
    try:
        result = await worker.send_message(
            messages.Message(content=f"agent{i}.py"), creator_id
        )
        with open(BASE_DIR / f"idea{i}.md", "w", encoding="utf-8") as f:
            f.write(result.content)
        return True
    except Exception as e:
        print(f"Failed to run worker {i} due to exception: {e}")
        return False


def plan_agent_batches() -> list[list[int]]:
    batches: list[list[int]] = []
    current_batch: list[int] = []

    for i in range(1, HOW_MANY_AGENTS + 1):
        current_batch.append(i)
        if i < HOW_MANY_AGENTS and random.random() < CHANCES_THAT_I_CHANGE_CREATOR:
            batches.append(current_batch)
            current_batch = []

    if current_batch:
        batches.append(current_batch)
    return batches


async def create_agents_with_evolving_creators(worker, creator_id):
    batches = plan_agent_batches()
    active_creator_id = creator_id
    agent_tasks = []

    for batch_number, batch in enumerate(batches):
        agent_tasks.extend(
            asyncio.create_task(create_and_message(worker, active_creator_id, i))
            for i in batch
        )
        if batch_number < len(batches) - 1:
            active_creator_id = await create_next_creator(
                worker, active_creator_id, batch_number + 1
            )

    await asyncio.gather(*agent_tasks)


async def main():
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start()
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()
    await Creator.register(worker, "Creator", lambda: Creator("Creator"))
    creator_id = AgentId("Creator", "default")
    await create_agents_with_evolving_creators(worker, creator_id)
    try:
        await worker.stop()
        await host.stop()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(main())
