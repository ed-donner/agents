import json
from openai import OpenAI
from date_client import call_date_tool, list_date_tools
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables from a .env file
load_dotenv()
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_base_url = os.getenv("OPENROUTER_BASE_URL")

# Retrieve and format the list of available tools
async def get_tools():
    tool_list = []
    tools = await list_date_tools()
    for tool in tools:
        # Build the tool schema for OpenAI function calling
        schema = {**tool.inputSchema, "additionalProperties": False}
        tool_name = {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                **schema
            }
        }
        tool_list.append(tool_name)
    return tool_list

# Handle tool calls and return their results
async def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
        print(f"Tool called: {tool_name}", flush=True)

        # Call the tool and get the result
        result = await call_date_tool(tool_name, tool_args)
        results.append({"role": "tool", "content": json.dumps(result.structuredContent), "tool_call_id": tool_call.id})
    return results

async def call_llm():
    client = OpenAI(
        base_url=openrouter_base_url,
        api_key=openrouter_api_key,
    )

    tools_list = await get_tools()
    tools = [{"type": "function", "function": {**tool}} for tool in tools_list]
    print("Tools to register with OpenAI:", tools)

    system_prompt = "You are a helpful assistant that can call tools to get the current date and time in various timezones."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "What is the current date and time in New York?"}
    ]
    
    done = False
    while not done:
        response = client.chat.completions.create(
            model="openai/gpt-4.1-mini",
            messages=messages,
            tools=tools,
        )

        finish_reason = response.choices[0].finish_reason

        if finish_reason == "tool_calls":
            print("LLM is calling tools...")
            message = response.choices[0].message
            print("LLM message with tool calls:", message)
            tool_calls = message.tool_calls
            tool_results = await handle_tool_calls(tool_calls)
            messages.append(message)
            messages.extend(tool_results)
        else:
            done = True

    return response.choices[0].message.content

if __name__ == "__main__":
    output = asyncio.run(call_llm())
    print("Final LLM response:", output)



