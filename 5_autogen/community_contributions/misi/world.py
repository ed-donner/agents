from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost
from creator import Creator
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from autogen_core import AgentId
import messages
import asyncio
from pathlib import Path
import random

HOW_MANY_AGENTS = 20
CHANCES_THAT_I_CHANGE_CREATOR = 0.5
BASE_DIR = Path(__file__).resolve().parent


async def create_next_creator(worker, creator_id, creator_number: int) -> AgentId:
    creator_name = f"creator{creator_number}"
    try:
        creator_result = await worker.send_message(messages.Message(content=f"{creator_name}.py"), creator_id)
        with open(BASE_DIR / f"{creator_name}.md", "w", encoding="utf-8") as f:
            f.write(creator_result.content)
        print(f"Switching future agent creation to {creator_name}")
        return AgentId(creator_name, "default")
    except Exception as e:
        print(f"Failed to create creator replica {creator_name} due to exception: {e}")
        return creator_id


async def create_and_message(worker, creator_id, i: int) -> bool:
    try:
        result = await worker.send_message(messages.Message(content=f"agent{i}.py"), creator_id)
        with open(BASE_DIR / f"idea{i}.md", "w", encoding="utf-8") as f:
            f.write(result.content)
        return True
    except Exception as e:
        print(f"Failed to run worker {i} due to exception: {e}")
        return False


async def create_agents_with_evolving_creators(worker, creator_id):
    active_creator_id = creator_id
    next_creator_number = 1

    for i in range(1, HOW_MANY_AGENTS + 1):
        created = await create_and_message(worker, active_creator_id, i)
        if created and i < HOW_MANY_AGENTS and random.random() < CHANCES_THAT_I_CHANGE_CREATOR:
            active_creator_id = await create_next_creator(worker, active_creator_id, next_creator_number)
            next_creator_number += 1

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
