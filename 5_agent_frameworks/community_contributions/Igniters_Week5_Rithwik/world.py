from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost
from agent import Agent
from creator import Creator
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from autogen_core import AgentId
import messages
import asyncio

HOW_MANY_AGENTS = 5
HOW_MANY_CREATORS = 3

async def create_and_message(worker, creator_id, i: int):
    try:
        result = await worker.send_message(messages.Message(content=f"agent{i}.py"), creator_id)
        with open(f"idea{i}.md", "w") as f:
            f.write(result.content)
    except Exception as e:
        print(f"Failed to run worker {i} due to exception: {e}")

# create more creators
async def create_creator(worker, creator_id, i: int):
    try:
        result = await worker.send_message(messages.Message(content=f"creator{i}.py"), creator_id)
        print(f"New creator{i} said: {result.content}")
    except Exception as e:
        print(f"Failed to create creator {i}: {e}")


async def main():
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start()
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()

    await Creator.register(worker, "Creator", lambda: Creator("Creator"))
    original_creator_id = AgentId("Creator", "default")

    creator_coroutines = [create_creator(worker, original_creator_id, i) for i in range(1, HOW_MANY_CREATORS + 1)]
    await asyncio.gather(*creator_coroutines)

    all_creator_ids = [AgentId("Creator", "default")] + [AgentId(f"creator{i}", "default") for i in range(1, HOW_MANY_CREATORS + 1)]

    agent_coroutines = [
        create_and_message(worker, all_creator_ids[i % len(all_creator_ids)], i)
        for i in range(1, HOW_MANY_AGENTS + 1)
    ]
    await asyncio.gather(*agent_coroutines)

    try:
        await worker.stop()
        await host.stop()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())