#!/usr/bin/env python3
import asyncio
import os
import sys

from dotenv import load_dotenv

from pipeline import TechEval


async def _run(question):
    if not os.environ.get("OPENAI_API_KEY"):
        print("set OPENAI_API_KEY first", file=sys.stderr)
        sys.exit(1)

    report = None
    async for chunk in TechEval().run(question):
        if chunk.startswith("[status] "):
            print(chunk.removeprefix("[status] "))
        else:
            report = chunk

    if report:
        print(report)


if __name__ == "__main__":
    load_dotenv(override=True)
    q = " ".join(sys.argv[1:]).strip()
    if not q:
        q = "Should we use htmx instead of React for our internal admin tools?"
    asyncio.run(_run(q))
