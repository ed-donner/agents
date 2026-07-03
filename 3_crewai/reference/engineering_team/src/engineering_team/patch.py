"""Monkey-patch for a CrewAI 1.14.4 bug where HTTPS MCP tool names are sanitized
on discovery but the sanitized name is then sent back to the server, so any
server tool whose name contains hyphens (e.g. Context7's `resolve-library-id`)
becomes unreachable. Re-verify on crewai upgrade.

Importing this module applies the patch as a side effect.
"""
import asyncio
from typing import Any, cast

from crewai.mcp.tool_resolver import MCPToolResolver
from crewai.tools.base_tool import BaseTool
from crewai.tools.mcp_tool_wrapper import MCPToolWrapper
from crewai.utilities.string_utils import sanitize_tool_name


def _resolve_external(self, mcp_ref: str) -> list[BaseTool]:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    if "#" in mcp_ref:
        server_url, specific_tool = mcp_ref.split("#", 1)
    else:
        server_url, specific_tool = mcp_ref, None

    server_params = {"url": server_url}
    server_name = self._extract_server_name(server_url)
    sanitized_specific = sanitize_tool_name(specific_tool) if specific_tool else None

    async def _list_mcp_tools() -> list[Any]:
        async with streamablehttp_client(server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return list((await session.list_tools()).tools)

    try:
        mcp_tools = asyncio.run(_list_mcp_tools())
    except Exception as e:
        self._logger.log("warning", f"Failed to connect to MCP server {server_url}: {e}")
        return []

    tools: list[BaseTool] = []
    for mcp_tool in mcp_tools:
        sanitized = sanitize_tool_name(mcp_tool.name)
        if sanitized_specific and sanitized != sanitized_specific:
            continue
        args_schema = None
        if getattr(mcp_tool, "inputSchema", None):
            args_schema = self._json_schema_to_pydantic(sanitized, mcp_tool.inputSchema)
        schema = {
            "description": getattr(mcp_tool, "description", ""),
            "args_schema": args_schema,
        }
        try:
            wrapper = MCPToolWrapper(
                mcp_server_params=server_params,
                tool_name=sanitized,
                tool_schema=schema,
                server_name=server_name,
            )
            # Preserve the unsanitized server-side name so call_tool reaches the real tool.
            wrapper._original_tool_name = mcp_tool.name
            tools.append(wrapper)
        except Exception as e:
            self._logger.log("warning", f"Failed to create MCP tool wrapper for {sanitized}: {e}")

    return cast(list[BaseTool], tools)


MCPToolResolver._resolve_external = _resolve_external
