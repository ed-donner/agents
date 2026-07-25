from contextlib import AsyncExitStack
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import os
import os.path

load_dotenv(override=True)

MCP_SERVER_PARAMS = {
    "command": "uv",
    "args": ["run", os.path.join(os.path.dirname(__file__), "reviewer_server.py")],
}

INSTRUCTIONS = """
You are an expert frontend code reviewer specialising in React, TypeScript, accessibility, security, and performance.

You have four analysis tools available:
- check_accessibility — detects a11y issues (missing alt, keyboard access, ARIA)
- check_security      — detects XSS vectors, hardcoded secrets, unsafe patterns
- check_performance   — detects React performance anti-patterns
- check_best_practices — detects TypeScript and React code quality issues

You also have tools to read files from disk if given a file path.

When given code to review:
1. Run all four checkers on the code
2. Synthesize the results into a clear, structured markdown report

Your report must follow this structure exactly:

---
# Code Review Report

## Summary
One paragraph covering the overall quality and the most important finding.

## Critical Issues
List each issue with: the problem, why it matters, and a concrete fix with a code example.
If none, write "None found."

## Warnings
List each warning with: the problem and a suggested improvement.
If none, write "None found."

## Quick Wins
2–3 small, easy improvements not already covered above.

## Verdict
One line: PASS / NEEDS WORK / MAJOR ISSUES — and one sentence of rationale.
---

Be specific. Reference the actual patterns found. Don't pad with generic advice.
"""


async def review_code(code: str) -> str:
    async with AsyncExitStack() as stack:
        server = await stack.enter_async_context(
            MCPServerStdio(MCP_SERVER_PARAMS, client_session_timeout_seconds=60)
        )
        agent = Agent(
            name="FrontendReviewer",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini",
            mcp_servers=[server],
        )
        with trace("frontend-code-review"):
            result = await Runner.run(agent, f"Please review this code:\n\n```\n{code}\n```")
        return result.final_output


async def review_file(path: str) -> str:
    async with AsyncExitStack() as stack:
        server = await stack.enter_async_context(
            MCPServerStdio(MCP_SERVER_PARAMS, client_session_timeout_seconds=60)
        )
        agent = Agent(
            name="FrontendReviewer",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini",
            mcp_servers=[server],
        )
        with trace("frontend-code-review"):
            if os.path.isdir(path):
                message = (
                    f"Use list_source_files to find all frontend files in {path}, "
                    f"then read and review each one. Produce one combined report covering all files found."
                )
            else:
                message = f"Please read and review the file at this path: {path}"
            result = await Runner.run(agent, message)
        return result.final_output
