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
            # Unwrap commonly returned shapes so callers get the inner value
            try:
                # Some MCP implementations return an object with a 'result' attr
                if hasattr(result, "result"):
                    return result.result
                # Or a mapping with a 'result' key
                if isinstance(result, dict) and "result" in result:
                    return result["result"]
            except Exception:
                # Fall back to returning the raw result
                pass
            return result

async def ask_llm(prompt: str):
    return await call_date_tool("ask_llm", {"prompt": prompt})

async def chat_mode():
    print("\n🤖 AI Chat Mode — type 'exit' to quit.\n")
    while True:
        msg = input("You: ")
        if msg.lower() in ["exit", "quit"]:
            break
        response = await ask_llm(msg)
        # response should be a string if server returned text; otherwise stringify
        try:
            out = response if isinstance(response, str) else str(response)
        except Exception:
            out = repr(response)
        print("\nAI:\n", out, "\n")