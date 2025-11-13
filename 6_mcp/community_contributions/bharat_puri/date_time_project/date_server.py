from datetime import date, datetime
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("date_server")


@mcp.tool()
async def current_date() -> str:
    """Return today's date in ISO format (YYYY-MM-DD)."""
    return date.today().isoformat()

@mcp.tool()
async def current_time() -> str:
    """Return the current time in UTC (HH:MM:SS)."""
    return datetime.utcnow().strftime("%H:%M:%S")
    

if __name__ == "__main__":
    mcp.run(transport="stdio")


# import anyio
# from datetime import datetime
# from mcp.server import Server
# from mcp.server.stdio import stdio_server
# from mcp.types import Tool, ToolInputSchema, ToolResult, TextContent

# server = Server(
#     name="date-server",
#     version="2.0.0",
#     instructions="A simple server that returns the current date and time."
# )

# # ---------------------------------------------
# # 1️⃣ Register list_tools
# # ---------------------------------------------
# @server.list_tools()
# async def list_tools():
#     return [
#         Tool(
#             name="current_date",
#             description="Get the current date in ISO format",
#             inputSchema=ToolInputSchema(type="object")
#         ),
#         Tool(
#             name="current_time",
#             description="Get the current time (UTC)",
#             inputSchema=ToolInputSchema(type="object")
#         )
#     ]

# # ---------------------------------------------
# # 2️⃣ Implement tool execution
# # ---------------------------------------------
# @server.call_tool()
# async def call_tool(name, args):
#     if name == "current_date":
#         value = datetime.utcnow().date().isoformat()

#     elif name == "current_time":
#         value = datetime.utcnow().strftime("%H:%M:%S UTC")

#     else:
#         value = f"Unknown tool: {name}"

#     return ToolResult(
#         content=[TextContent(type="text", text=value)],
#         isError=False
#     )

# # ---------------------------------------------
# # 3️⃣ Run MCP server
# # ---------------------------------------------
# async def main():
#     async with stdio_server(server) as (read_stream, write_stream):
#         await server.run(
#             read_stream,
#             write_stream,
#             initialization_options=server.create_initialization_options(),
#             raise_exceptions=False
#         )

# if __name__ == "__main__":
#     anyio.run(main)
