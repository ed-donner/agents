import asyncio
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv(override=True)

# Setup OpenAI client
client = OpenAI()

async def run_date_client():
    # Path to the server script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "date_server.py")

    # MCP Server parameters
    params = StdioServerParameters(
        command="uv",
        args=["run", server_path],
        env=None
    )

    # Establish connection to the MCP server
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            # Initialize MCP session
            await session.initialize()

            # 1. Discover available tools from the server
            tools_result = await session.list_tools()
            mcp_tools = tools_result.tools

            # 2. Convert MCP tools to OpenAI function tool format
            openai_tools = []
            for tool in mcp_tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            # 3. Native OpenAI call
            messages = [{"role": "user", "content": "What is today's date?"}]

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=openai_tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # 4. Handle tool calls if the model requested them
            if tool_calls:
                messages.append(response_message)

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    print(f"Calling MCP tool: {function_name} with args: {function_args}")

                    # Call the tool via the MCP session
                    tool_result = await session.call_tool(function_name, function_args)

                    # The result from MCP is typically a list of content blocks
                    result_text = tool_result.content[0].text if tool_result.content else "No result"

                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": result_text,
                    })

                # Final response from the model after getting tool results
                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                )
                print(f"Final Answer: {final_response.choices[0].message.content}")
            else:
                print(f"Response: {response_message.content}")

if __name__ == "__main__":
    asyncio.run(run_date_client())
