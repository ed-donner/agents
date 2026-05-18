import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from anthropic import Anthropic

server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)

async def run_analyst():
    client = Anthropic(api_key="ANTHROPIC_API_KEY")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            
            prompt = "Analyze the performance of AAPL. Fetch the price and sentiment first."
            
        
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                tools=[{
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema
                } for t in tools.tools],
                messages=[{"role": "user", "content": prompt}]
            )

            print(f"\nAI Analyst response:\n{response.content[0].text}")
            
            for content in response.content:
                if content.type == "tool_use":
                    tool_name = content.name
                    tool_args = content.input
                    
                    result = await session.call_tool(tool_name, tool_args)
                    print(f"\n[Tool Call] {tool_name}({tool_args}) -> {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(run_analyst())