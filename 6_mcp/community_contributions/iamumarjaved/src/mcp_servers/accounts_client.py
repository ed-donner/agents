from agents.mcp import MCPServerStdio
from src.utils.mcp_params import trader_mcp_server_params

async def get_accounts_tools_openai():
    params = {"command": "uv", "args": ["run", "src/mcp_servers/accounts_server.py"]}
    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        mcp_tools = await server.list_tools()
    return mcp_tools

async def list_accounts_tools():
    params = {"command": "uv", "args": ["run", "src/mcp_servers/accounts_server.py"]}
    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        tools = await server.list_tools()
    return [tool.name for tool in tools]

async def read_accounts_resource(name: str) -> str:
    params = {"command": "uv", "args": ["run", "src/mcp_servers/accounts_server.py"]}
    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        resources = await server.list_resources()
        for resource in resources:
            if resource.uri == f"accounts://accounts_server/{name.lower()}":
                content = await server.read_resource(resource.uri)
                return content.contents[0].text
    return "{}"

async def read_strategy_resource(name: str) -> str:
    params = {"command": "uv", "args": ["run", "src/mcp_servers/accounts_server.py"]}
    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        resources = await server.list_resources()
        for resource in resources:
            if resource.uri == f"accounts://strategy/{name.lower()}":
                content = await server.read_resource(resource.uri)
                return content.contents[0].text
    return ""
