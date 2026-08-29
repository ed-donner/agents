#!/usr/bin/env python3
"""
CLI entry point for the Primemash Marketing Agent System.
Usage:
  python main.py                        # Interactive mode
  python main.py "Post today's content" # Single task
  python main.py --daily                # Run daily posting cycle
  python main.py --analytics            # Generate analytics report
  python main.py --serve                # Start the API server
"""

import asyncio
import sys
import uvicorn
from dotenv import load_dotenv

load_dotenv()


async def run_task(task: str):
    from src.agents.marketing_team import run_agent_task
    print(f"\n🤖 Running: {task}\n{'─' * 60}")
    result = await run_agent_task(task)
    print(f"\n✅ Result:\n{result}\n")


def main():
    args = sys.argv[1:]

    if "--serve" in args:
        print("🚀 Starting Primemash Marketing API on http://localhost:8000")
        uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
        return

    if "--daily" in args:
        asyncio.run(run_task(
            "Generate and publish today's content for LinkedIn, Twitter, and Instagram. "
            "One post per platform. Use today's content theme."
        ))
        return

    if "--analytics" in args:
        asyncio.run(run_task(
            "Generate a detailed analytics report with performance insights "
            "and 3 actionable recommendations for next week."
        ))
        return

    if args:
        # Task passed as argument
        asyncio.run(run_task(" ".join(args)))
        return

    # Interactive mode
    print("🤖 Primemash Marketing Agent — Interactive Mode")
    print("Type 'exit' to quit.\n")
    while True:
        try:
            task = input("Task: ").strip()
            if task.lower() in ("exit", "quit"):
                break
            if task:
                asyncio.run(run_task(task))
        except KeyboardInterrupt:
            break
    print("\nGoodbye!")


if __name__ == "__main__":
    main()
