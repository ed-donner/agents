from __future__ import annotations

import argparse
import os
from contextlib import AsyncExitStack
from datetime import datetime

from agents import Agent, Runner, Tool, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv(override=True)

SERVER_PATH = os.path.abspath("mcp_assessment_server.py")
ASSESSMENT_SERVER_PARAMS = {"command": "python", "args": [SERVER_PATH]}


def get_research_params() -> dict:
    brave_api_key = os.getenv("BRAVE_API_KEY")
    if brave_api_key:
        return {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": {"BRAVE_API_KEY": brave_api_key},
        }
    return {"command": "uvx", "args": ["mcp-server-fetch"]}


async def make_researcher_tool(mcp_servers: list[MCPServerStdio]) -> Tool:
    researcher = Agent(
        name="Researcher",
        model="gpt-4.1-mini",
        instructions=(
            "You are an equity due-diligence researcher.\n"
            "Research the requested company and persist facts using MCP tools.\n"
            "You must call register_company before any save_* calls.\n"
            "Store at least 4 findings with confidence scores.\n"
            "Store at least 2 meaningful risks with mitigations.\n"
            f"Current UTC date: {datetime.utcnow().strftime('%Y-%m-%d')}"
        ),
        mcp_servers=mcp_servers,
    )
    return researcher.as_tool(
        tool_name="Researcher",
        tool_description=(
            "Researches a company and stores findings/risks in the assessment MCP server."
        ),
    )


async def make_analyst_tool(mcp_servers: list[MCPServerStdio]) -> Tool:
    analyst = Agent(
        name="Analyst",
        model="gpt-4.1-mini",
        instructions=(
            "You are a disciplined investment analyst.\n"
            "Read assessment://rubric and assessment://company/{symbol} resources.\n"
            "Then add one recommendation using save_recommendation.\n"
            "Finalize with finalize_assessment using a score between 0 and 100 and verdict "
            "in {buy, hold, avoid}.\n"
            "Explain trade-offs, upside/downside, and catalyst timing in concise bullet points."
        ),
        mcp_servers=mcp_servers,
    )
    return analyst.as_tool(
        tool_name="Analyst",
        tool_description="Produces final score, verdict, and recommendation for a company.",
    )


async def run_assessment(query: str) -> str:
    async with AsyncExitStack() as stack:
        assessment_server = await stack.enter_async_context(
            MCPServerStdio(params=ASSESSMENT_SERVER_PARAMS, client_session_timeout_seconds=90)
        )
        research_server = await stack.enter_async_context(
            MCPServerStdio(params=get_research_params(), client_session_timeout_seconds=90)
        )

        researcher_tool = await make_researcher_tool([assessment_server, research_server])
        analyst_tool = await make_analyst_tool([assessment_server])

        coordinator = Agent(
            name="AssessmentCoordinator",
            model="gpt-4.1-mini",
            tools=[researcher_tool, analyst_tool],
            instructions=(
                "Coordinate a complete due-diligence run.\n"
                "Workflow:\n"
                "1) Use Researcher first.\n"
                "2) Then use Analyst.\n"
                "3) Return a concise investment memo with score, verdict, and key risks.\n"
                "Never skip tool usage."
            ),
        )

        with trace("mideseniordev_mcp_assessment"):
            result = await Runner.run(coordinator, query, max_turns=35)
            return result.final_output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MCP due-diligence assessment workflow.")
    parser.add_argument(
        "query",
        nargs="?",
        default="Assess Microsoft (MSFT) as a long-term investment opportunity.",
        help="Prompt for the assessment coordinator.",
    )
    args = parser.parse_args()

    import asyncio

    output = asyncio.run(run_assessment(args.query))
    print(output)


if __name__ == "__main__":
    main()
