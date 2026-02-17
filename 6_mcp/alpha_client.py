import mcp
from mcp.client.streamable_http import streamablehttp_client
from agents import FunctionTool
import json
import base64
import os

config = {
  "alphaVantageApiKey": os.getenv("ALPHA_VANTAGE_API_KEY")
}
# Encode config in base64
config_b64 = base64.b64encode(json.dumps(config).encode())
smithery_api_key = os.getenv("SMITHERY_API_KEY")

# Create server URL
url = f"https://server.smithery.ai/@qubaomingg/stock-analysis-mcp/mcp?config={config_b64}&api_key={smithery_api_key}"

# Create a streamable HTTP client for the MCP server
# This allows us to use the MCP client with a streamable HTTP connection
async def list_stock_tools():
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools
        
async def call_stock_tool(tool_name, tool_args):
    print(f"Calling {tool_name} with {tool_args}")
    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with mcp.ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            print(f"Result: {result}")
            return result
        
async def get_stock_tools_openai():
    openai_tools = []
    for tool in await list_stock_tools():
        schema = {**tool.inputSchema, "additionalProperties": False}
        schema["properties"] = {"symbol":schema["properties"]["symbol"]}
        openai_tool = FunctionTool(
            name=tool.name,
            description=tool.name.replace("-", " "),
            params_json_schema=schema,
            on_invoke_tool=lambda ctx, args, toolname=tool.name: call_stock_tool(toolname, json.loads(args))
                
        )
        openai_tools.append(openai_tool)
    return openai_tools
