"""
 client.py - Healthcare MCP Client
 Connects to the MCP server and via stdio, lists available tools
 and exposes a clean async interface for calling them
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = __file__.replace("client.py", "medical_patient_mgt_mcp_server.py")

async def get_session():
    """Create and return an active MCP client session (context manager)."""
    server_params = StdioServerParameters(
        command="python",
        args=[SERVER_SCRIPT],
    )
    return stdio_client(server_params)


async def list_tools() -> list[dict]:
    """Return all tools exposed by the MCP server."""
    server_params = StdioServerParameters(
        command="python",
        args=[SERVER_SCRIPT],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema.get("properties", {}) if tool.inputSchema else [],
                    "required": tool.inputSchema.get("required", []) if tool.inputSchema else [],

                } for tool in tools_response.tools
            ]
        

async def call_tool(tool_name: str, arguments: dict) -> dict:
    """Call a specific MCP tool with given arguments."""
    server_params = StdioServerParameters(
        command="python",
        args=[SERVER_SCRIPT],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            # Parse text content from result
            if result.content:
                text = result.content[0].text
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"result": text}
               
            return {"result": None}
        

async def print_tools():
    """Pretty-print all available tools."""
    tools = await list_tools()
    print(f"\n{'='*60}")
    print(f" healthcare MCP Server - {len(tools)} tool available")
    print(f"{'='*60}")
    for i, tool in enumerate(tools, 1):
        print(f"\n  {i:02}. {tool['name']}")
        print(f"    {tool['description']}")
        if tool["required"]:
            print(f"    Required params: {', '.join(tool['required'])}")

        optional = [k for k in tool["parameters"] if k not in tool["required"]]             
        if optional:
            print(f"    Optional params: {', '.join(optional)}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    async def main():
        print("\n[1] Listing all tools from the Healthcare MCP Server...\n")
        await print_tools()

        print("[2] Quick smoke test - calling list_staff as admin...\n")

        result = await call_tool("list_staff", {
            "admin_email": "admin@vendor.com",
            "admin_password": "admin1234"
            })
        count = len(result.get("staff", []))
        print(f"  Result: {result['status']} - {count} staff member(s) found in database.\n")

    
    asyncio.run(main())