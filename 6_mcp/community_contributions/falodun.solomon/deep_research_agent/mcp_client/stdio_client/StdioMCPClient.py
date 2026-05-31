import asyncio
from typing import Any, Dict

from mcp import ClientSession
from agents.mcp import MCPServerStdio


class StdioMCPClient:

    def __init__(self, params: Dict[str, Any], timeout: int = 30):
        self.params = params
        self.timeout = timeout
        self.session: ClientSession | None = None
        self.server_ctx = None

    async def connect(self):
        self.server_ctx = MCPServerStdio(
            params=self.params,
            client_session_timeout_seconds=self.timeout
        )

        self.session = await self.server_ctx.__aenter__()

    async def close(self):
        if self.server_ctx:
            await self.server_ctx.__aexit__(None, None, None)

    async def list_tools(self):
        tools = await self.session.list_tools()
        return tools

    async def invoke(self, tool_name: str, payload: dict):
        return await self.session.call_tool(tool_name, payload)