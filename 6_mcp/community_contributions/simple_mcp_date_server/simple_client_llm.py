# uv init simple_mcp_date_Server 
# cd simple_mcp_date_server 
# uv venv 
# source .venv/bin/activate or .venv\Scripts\activate 
# uv add mcp anthropic python-dotenv
# uv run simple_client.py


import asyncio
import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv


load_dotenv()

async def main():
    """Use Anthropic API with MCP tools to get the current date."""
    
    # Initialize Anthropic client
    client = anthropic.Anthropic()
    
    # Define server parameters
    server_params = StdioServerParameters(
        command="uv",
        args=["run","server.py"],
    )
    
    # Connect to the MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools from the server
            tools_list = await session.list_tools()
            
            # Convert MCP tools to Anthropic tool format
            tools = []
            for tool in tools_list.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            
            print("Available MCP tools:", [t["name"] for t in tools])
            print()
            
            # Make the initial request to Claude
            messages = [
                {"role": "user", "content": "What is today's date? Use the available tool to find out."}
            ]
            
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                tools=tools,
                messages=messages
            )
            
            print(f"Claude's initial response: {response.stop_reason}")
            
            # Process tool calls
            while response.stop_reason == "tool_use":
                # Add assistant's response to messages
                messages.append({"role": "assistant", "content": response.content})
                
                # Execute each tool call
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        
                        print(f"Calling tool: {tool_name} with input: {tool_input}")
                        
                        # Call the MCP tool
                        result = await session.call_tool(tool_name, arguments=tool_input)
                        
                        # Extract the text content from the result
                        tool_result_text = result.content[0].text
                        print(f"Tool result: {tool_result_text}")
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result_text
                        })
                
                # Add tool results to messages
                messages.append({"role": "user", "content": tool_results})
                
                # Continue the conversation with tool results
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=1024,
                    tools=tools,
                    messages=messages
                )
            
            # Print final response
            print("\nClaude's final response:")
            for block in response.content:
                if hasattr(block, "text"):
                    print(block.text)


if __name__ == "__main__":
    asyncio.run(main())