from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost
from agent import Agent
from creator import Creator
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from autogen_core import AgentId
import messages
import asyncio
from pathlib import Path

HOW_MANY_AGENTS = 20
BASE_DIR = Path(__file__).resolve().parent


async def create_creator_and_agent(worker, creator_id):
    try:
        creator_result = await worker.send_message(messages.Message(content="creator1.py"), creator_id)
        with open(BASE_DIR / "creator1.md", "w", encoding="utf-8") as f:
            f.write(creator_result.content)

        new_creator_id = AgentId("creator1", "default")
        result = await worker.send_message(messages.Message(content="agent_from_creator1.py"), new_creator_id)
        with open(BASE_DIR / "idea_from_creator1.md", "w", encoding="utf-8") as f:
            f.write(result.content)
    except Exception as e:
        print(f"Failed to create a creator replica due to exception: {e}")


async def create_and_message(worker, creator_id, i: int):
    try:
        result = await worker.send_message(messages.Message(content=f"agent{i}.py"), creator_id)
        with open(BASE_DIR / f"idea{i}.md", "w", encoding="utf-8") as f:
            f.write(result.content)
    except Exception as e:
        print(f"Failed to run worker {i} due to exception: {e}")

async def main():
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start() 
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()
    result = await Creator.register(worker, "Creator", lambda: Creator("Creator"))
    creator_id = AgentId("Creator", "default")
    await create_creator_and_agent(worker, creator_id)
    coroutines = [create_and_message(worker, creator_id, i) for i in range(1, HOW_MANY_AGENTS+1)]
    await asyncio.gather(*coroutines)
    try:
        await worker.stop()
        await host.stop()
    except Exception as e:
        print(e)




if __name__ == "__main__":
    asyncio.run(main())
