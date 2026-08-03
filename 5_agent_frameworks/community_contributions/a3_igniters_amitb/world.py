from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost
from creator import Creator
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from autogen_core import AgentId
import messages
import asyncio

HOW_MANY_AGENTS = 4

async def create_and_message(worker, creator_id, name: int = 1):
    try:
        result = await worker.send_message(messages.Message(content=f"agent_{name}.py"), creator_id)
        with open(f"idea_{name}.md", "w") as f:
            f.write(result.content)
    except Exception as e:
        print(f"Failed to run worker {name} due to exception: {e}")

async def main():
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start() 
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()
    result = await Creator.register(worker, "Creator", lambda: Creator("Creator"))
    creator_id = AgentId("Creator", "default")
    coroutines = [create_and_message(worker, creator_id, name) for name in range(1, HOW_MANY_AGENTS+1)]
    await asyncio.gather(*coroutines)
    try:
        await worker.stop()
        await host.stop()
    except Exception as e:
        print(e)




if __name__ == "__main__":
    asyncio.run(main())


