from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost, GrpcWorkerAgentRuntime
from autogen_core import AgentId
from creator import Creator
import messages
import asyncio
import os

# ── Configure your job search here ───────────────────────────────────────────

JOB_ROLE = """
Senior Frontend Engineer at a fintech scale-up.

Responsibilities:
- Lead architecture decisions for a React/TypeScript web application
- Work closely with product and design to ship user-facing features
- Mentor junior engineers and conduct code reviews
- Own performance, accessibility, and security for the frontend

Stack: React, TypeScript, Next.js, REST APIs, GitHub Actions, Vercel
"""

HOW_MANY_AGENTS = 10
OUTPUT_DIR = "output"

# ─────────────────────────────────────────────────────────────────────────────


async def create_and_interview(worker, creator_id, i: int):
    try:
        message_content = f"agent{i}.py|||{JOB_ROLE}"
        result = await worker.send_message(
            messages.Message(content=message_content), creator_id
        )
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(f"{OUTPUT_DIR}/questions{i}.md", "w", encoding="utf-8") as f:
            f.write(f"# Interview Questions — Interviewer {i}\n\n")
            f.write(f"**Role:** {JOB_ROLE.strip()}\n\n---\n\n")
            f.write(result.content)
        print(f"Saved questions{i}.md")
    except Exception as e:
        print(f"Agent {i} failed: {e}")


async def main():
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    host.start()

    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
    await worker.start()

    await Creator.register(worker, "Creator", lambda: Creator("Creator"))
    creator_id = AgentId("Creator", "default")

    coroutines = [
        create_and_interview(worker, creator_id, i)
        for i in range(1, HOW_MANY_AGENTS + 1)
    ]
    await asyncio.gather(*coroutines)

    try:
        await worker.stop()
        await host.stop()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(main())
