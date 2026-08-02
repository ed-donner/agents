import os
import json
import asyncio
import contextlib
from typing import List, Optional, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from tracers import LogTracer
from database import write_log

# The path to the github_server.py
SERVER_PATH = os.path.join(os.path.dirname(__file__), "github_server.py")

class GitHubClientBridge:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", SERVER_PATH],
            env={**os.environ, "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "dummy_token")}
        )
        self.tracer = LogTracer()
        self._exit_stack = contextlib.AsyncExitStack()

    async def connect(self):
        """Initialize the stdio client session."""
        try:
            stdio_transport = await self._exit_stack.enter_async_context(stdio_client(self.server_params))
            self.session = await self._exit_stack.enter_async_context(ClientSession(stdio_transport[0], stdio_transport[1]))
            await self.session.initialize()
            write_log("github_agent", "info", "Successfully connected to GitHub MCP server")
        except Exception as e:
            write_log("github_agent", "error", f"Failed to connect to GitHub MCP server: {e}")
            raise

    async def disconnect(self):
        """Shutdown the session."""
        await self._exit_stack.aclose()
        self.session = None

    async def get_github_tools_openai(self) -> List[dict]:
        """
        Retrieve MCP tools and convert them to OpenAI-compatible function schemas.
        """
        if not self.session:
            return []

        mcp_tools = await self.session.list_tools()
        openai_tools = []

        for tool in mcp_tools.tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })
        return openai_tools

    async def read_github_resource(self, uri: str) -> str:
        """
        Retrieve data for a given GitHub MCP resource URI.
        """
        if not self.session:
            raise RuntimeError("Client session not connected")

        # Wrap in tracing
        try:
            resource = await self.session.read_resource(uri)
            content = resource.content[0].text if resource.content else ""
            write_log("github_agent", "resource", f"Read resource {uri}: {content[:100]}...")
            return content
        except Exception as e:
            write_log("github_agent", "error", f"Error reading resource {uri}: {e}")
            raise

    async def execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        Execute a tool on the GitHub MCP server.
        """
        if not self.session:
            raise RuntimeError("Client session not connected")

        # Wrap in tracing
        try:
            result = await self.session.call_tool(tool_name, arguments)
            text_result = result.content[0].text if result.content else ""
            write_log("github_agent", "tool", f"Executed {tool_name} with args {arguments}: {text_result[:100]}...")
            return text_result
        except Exception as e:
            write_log("github_agent", "error", f"Error executing tool {tool_name}: {e}")
            raise

# Singleton for easy access
github_bridge = GitHubClientBridge()

if __name__ == "__main__":
    async def main():
        bridge = GitHubClientBridge()
        try:
            await bridge.connect()
            tools = await bridge.get_github_tools_openai()
            print(f"Retrieved {len(tools)} tools")
            for tool in tools:
                print(f"- {tool['function']['name']}: {tool['function']['description']}")
        finally:
            await bridge.disconnect()

    asyncio.run(main())
