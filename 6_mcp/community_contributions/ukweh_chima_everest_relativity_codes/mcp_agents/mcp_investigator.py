import asyncio
import os
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

async def main():
    load_dotenv(override=True)
    
    # Paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sandbox_path = os.path.join(current_dir, "sandbox")
    os.makedirs(sandbox_path, exist_ok=True)
    
    # MCP server configurations
    files_params = {
        "command": "npx", 
        "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox_path]
    }
    
    # We use a second server (e.g., fetch) for web investigation
    fetch_params = {
        "command": "uvx", 
        "args": ["mcp-server-fetch"]
    }

    instructions = """
    You are a professional Investigator with access to multiple tool servers.
    1. Begin by fetching information from the web if required using the fetch tools.
    2. Analyze the data and write a detailed report.
    3. Use the filesystem tools to save your report to 'final_report.md' in the sandbox.
    4. Your final output should be a summary of what you did.
    """

    print("🚀 Starting Multi-Server MCP Agent...")
    
    async with MCPServerStdio(params=files_params) as files_server, \
               MCPServerStdio(params=fetch_params) as fetch_server:
        
        agent = Agent(
            name="multi_tool_investigator", 
            instructions=instructions, 
            model="gpt-4o-mini",
            mcp_servers=[files_server, fetch_server]
        )
        
        task = "Research the main features of the Model Context Protocol and save the findings to final_report.md"
        
        with trace("investigation_run"):
            result = await Runner.run(agent, task)
            print("\n✅ Task Complete!")
            print(f"Investigator Summary: {result.final_output}")

if __name__ == "__main__":
    asyncio.run(main())
