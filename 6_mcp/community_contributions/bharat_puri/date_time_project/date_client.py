import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters


params = StdioServerParameters(command="uv", args=["run", "date_server.py"], env=None)


async def list_date_tools():
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools


async def call_date_tool(tool_name, tool_args=None):
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args or {})
            return result


# import sys
# import asyncio
# from mcp.client.stdio import stdio_client, StdioServerParameters
# from mcp.client.session import ClientSession

# # ---------------------------------------------------------------
# # Helper: Extract clean text from MCP ToolResult (robust version)
# # ---------------------------------------------------------------
# def extract_text(result):
#     """
#     Extract text from ToolResult for ANY MCP SDK version.
#     """
#     contents = []

#     # MCP 1.0 older: result.content
#     if hasattr(result, "content") and result.content:
#         contents = result.content

#     # MCP 1.1 newer: result.contents
#     elif hasattr(result, "contents") and result.contents:
#         contents = result.contents

#     texts = []
#     for c in contents:
#         txt = (
#             getattr(c, "text", None)
#             or getattr(c, "value", None)
#             or getattr(c, "data", None)
#         )
#         if txt is None:
#             txt = str(c)
#         texts.append(txt)

#     return " ".join(texts)


# # ---------------------------------------------------------------
# # Client: List Tools
# # ---------------------------------------------------------------
# async def list_date_tools():
#     params = StdioServerParameters(command=sys.executable, args=["date_server.py"])

#     async with stdio_client(params) as (reader, writer):
#         async with ClientSession(reader, writer) as session:
#             result = await session.list_tools()
#             return result.tools


# # ---------------------------------------------------------------
# # Client: Call a tool and return clean string
# # ---------------------------------------------------------------
# async def call_date_tool(tool_name):
#     params = StdioServerParameters(command=sys.executable, args=["date_server.py"])

#     async with stdio_client(params) as (reader, writer):
#         async with ClientSession(reader, writer) as session:
#             result = await session.call_tool(tool_name, {})
#             return extract_text(result)
