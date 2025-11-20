# uv init simple_mcp_date_Server 
# cd simple_mcp_date_server 
# uv venv 
# source .venv/bin/activate or .venv\Scripts\activate 
# uv add mcp 
# uv run simple_client.py


import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """Connect to the date server and get the current date."""
    
    # Define server parameters - points to your server.py
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "server.py"],
    )
    
    # Connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()
            
            # Call the current_date tool
            result = await session.call_tool("current_date", arguments={})
            
            # Display the result
            print(f"Current date: {result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
