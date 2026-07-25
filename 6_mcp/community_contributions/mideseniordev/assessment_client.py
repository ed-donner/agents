from __future__ import annotations

import asyncio
import json
import os

import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_PATH = os.path.abspath("mcp_assessment_server.py")
PARAMS = StdioServerParameters(command="python", args=[SERVER_PATH], env=None)


async def inspect_server() -> None:
    async with stdio_client(PARAMS) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")

            await session.call_tool(
                "register_company",
                {
                    "symbol": "NFLX",
                    "name": "Netflix, Inc.",
                    "sector": "Communication Services",
                    "thesis": "Global streaming leader with pricing power and ad growth optionality.",
                },
            )
            await session.call_tool(
                "save_finding",
                {
                    "symbol": "NFLX",
                    "source": "10-K",
                    "finding": "Operating margin expansion has accelerated over the last two years.",
                    "confidence": 4,
                },
            )
            await session.call_tool(
                "save_risk",
                {
                    "symbol": "NFLX",
                    "risk": "Content cost inflation could pressure free cash flow.",
                    "severity": "medium",
                    "mitigation": "Improve ad tier monetization and maintain pricing discipline.",
                },
            )
            await session.call_tool(
                "finalize_assessment",
                {"symbol": "NFLX", "verdict": "hold", "score": 72},
            )

            company = await session.read_resource("assessment://company/NFLX")
            leaderboard = await session.read_resource("assessment://leaderboard")

            company_payload = json.loads(company.contents[0].text)
            leaderboard_payload = json.loads(leaderboard.contents[0].text)

            print("\nCompany snapshot:")
            print(json.dumps(company_payload, indent=2))
            print("\nLeaderboard:")
            print(json.dumps(leaderboard_payload, indent=2))


if __name__ == "__main__":
    asyncio.run(inspect_server())
