import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters


params = StdioServerParameters(command="python", args=["server.py"])
 
async def call_tool(tool_name, arguments):
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return result.content[0].text

class UseClient:
    async def askGPT(self, prompt):
        return await call_tool("ask_gpt", {"prompt": prompt})
    
    async def webSearch(self, query):
        return await call_tool("web_search", {"query": query})  
    
    async def smartSearch(self, question):
        return await call_tool("smart_search", {"question": question})


async def main():
    client = UseClient()
    gpt_response = await client.askGPT("What is the capital of Nigerias?")
    print(gpt_response)

if __name__ == "__main__":
    asyncio.run(main())