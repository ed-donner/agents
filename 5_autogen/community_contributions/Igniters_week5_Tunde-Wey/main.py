"""
Week 5 Igniters: distributed AutoGen Core runtime + Creator-authored AgentChat agents.

1. Start gRPC host + worker
2. Register Creator
3. Creator writes scout.py / synthesizer.py / closer.py and registers each
4. Kick off collaboration (agents message each other by AgentId name)
"""

from __future__ import annotations

import asyncio

from autogen_core import AgentId
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime, GrpcWorkerAgentRuntimeHost

import messages
from creator import Creator


async def main() -> None:
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start()

    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()

    try:
        await Creator.register(worker, "Creator", lambda: Creator("Creator"))
        creator_id = AgentId("Creator", "default")

        for stem in messages.ROSTER:
            result = await worker.send_message(messages.Message(content=f"{stem}.py"), creator_id)
            print(result.content)
            print("---")

        kickoff = (
            "Team goal: produce one sharp commercial business idea for the AI agents market "
            "(buyers, offer, pricing angle). Build on prior messages if any. "
            "You may already reach peers by name via the runtime — use that behavior when helpful."
        )
        first = messages.ROSTER[0]
        finale = await worker.send_message(messages.Message(content=kickoff), AgentId(first, "default"))
        print(f"\n=== Kickoff reply from {first} ===\n{finale.content}\n")

        second = messages.ROSTER[1]
        bridge = await worker.send_message(
            messages.Message(
                content=(
                    f"{first} said:\n{finale.content}\n\n"
                    "Integrate this into a tighter product + GTM sketch. "
                    "If your handler contacts a peer by name, use it to stress-test the idea."
                )
            ),
            AgentId(second, "default"),
        )
        print(f"=== Follow-up from {second} ===\n{bridge.content}\n")

        third = messages.ROSTER[2]
        closer = await worker.send_message(
            messages.Message(
                content=(
                    f"Thread:\n[{first}]\n{finale.content}\n\n[{second}]\n{bridge.content}\n\n"
                    "As the closer: merge into one commercial concept (name, buyer, offer, why now). "
                    "Peers may still be consulted by name inside your implementation if useful."
                )
            ),
            AgentId(third, "default"),
        )
        print(f"=== Synthesis from {third} ===\n{closer.content}\n")

    finally:
        await worker.stop()
        await host.stop()


if __name__ == "__main__":
    asyncio.run(main())
