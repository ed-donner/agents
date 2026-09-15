import sys
import mcp
from pathlib import Path
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters


if sys.platform.startswith("win"):
    # Under Windows, IPykernel's sys.stderr is not backed by a real file
    # descriptor. Redirect errlog to DEVNULL to avoid
    #   io.UnsupportedOperation: fileno
    # when stdio_client creates its subprocess.
    try:
        from IPython import get_ipython

        if get_ipython().__class__.__name__ == "ZMQInteractiveShell":
            import functools
            import subprocess

            # we are running inside Jupyter under Windows so redirect errlog
            stdio_client = functools.partial(
                stdio_client,
                errlog=subprocess.DEVNULL,
            )
    except (ImportError, ModuleNotFoundError, AttributeError, ):
        pass

params = StdioServerParameters(
    command="uv",
    args=["run", "-m", "backend.accounts_server"],
    cwd=str(Path(__file__).resolve().parent.parent),
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
