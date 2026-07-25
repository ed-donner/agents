import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path

_KICA = Path(__file__).resolve().parent

params = StdioServerParameters(
    command="uv",
    args=["run", str(_KICA / "accounts_server_crypto.py")],
    env=None,
)


async def read_accounts_resource(name):
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"accounts://accounts_server/{name}")
            return result.contents[0].text


async def read_strategy_resource(name):
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"accounts://strategy/{name}")
            return result.contents[0].text
