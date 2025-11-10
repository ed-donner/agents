
import asyncio
from mcp.client.fastmcp import FastMCPClient

async def run_client():
    client = FastMCPClient("accounts_server")
    await client.start("python server.py")

    result = await client.call_tool("city_temp", {"city": "Nairobi"})
    print("Temperature in Nairobi:", result)

    await client.stop()

if __name__ == "__main__":
    asyncio.run(run_client())
