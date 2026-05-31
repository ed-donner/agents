import asyncio
from mcp.client.stdio import stdio_client, ClientSession

async def main():
    params = {
        "command": "python",
        "args": ["server.py"]
    }

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            tools = await session.list_tools()
            print("Tools:", tools)

            result = await session.call_tool(
                "log_runbook_step",
                {"step": "Restart deployment"}
            )
            print(result)

asyncio.run(main())