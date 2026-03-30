import asyncio
import json
import sys
from pathlib import Path

import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
PARAMS = StdioServerParameters(
    command=sys.executable,
    args=[str(HERE / "server.py")],
    cwd=str(HERE),
)


async def main():
    async with stdio_client(PARAMS) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()




            tools = (await session.list_tools()).tools
            print("tools:", [t.name for t in tools])

            res = await session.call_tool("recommend", {
                "bean_code": "ETH-YRG",
                "roast_level": "light",
                "method": "pourover",
            })



            text = "\n".join(
                getattr(c, "text", str(c)) for c in (res.content or [])
            )

            
            try:
                print(json.dumps(json.loads(text), indent=2))
            except json.JSONDecodeError:
                print(text)


if __name__ == "__main__":
    asyncio.run(main())
