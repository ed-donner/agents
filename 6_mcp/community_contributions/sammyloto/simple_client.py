"""
Exercise the Agronomy MCP server without an LLM.

Run from this directory: python simple_client.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_ROOT = Path(__file__).resolve().parent


async def main() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(_ROOT / "mcp_server.py")],
        cwd=str(_ROOT),
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Agronomy MCP — tool smoke test")
            print("=" * 50)
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}")
            print()

            r = await session.call_tool(
                "compute_gdd_sum",
                arguments={
                    "zone_code": "HRV-HIGH",
                    "crop_code": "maize",
                    "start_date_iso": "2026-03-01",
                    "end_date_iso": "2026-06-30",
                },
            )
            print("compute_gdd_sum:", r.content[0].text)
            print()

            r = await session.call_tool(
                "integrated_field_brief",
                arguments={
                    "zone_code": "SAV-MID",
                    "soil_texture": "sandy_loam",
                    "crop_code": "common_bean",
                    "area_ha": 2.5,
                },
            )
            print("integrated_field_brief:", r.content[0].text)
            print()

            res = await session.list_resources()
            for res_item in res.resources:
                print("resource:", res_item.uri)
            print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
