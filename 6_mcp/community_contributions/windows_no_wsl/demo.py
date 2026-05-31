"""
Demonstration of winpatch enabling MCP servers on Windows.

This script shows both uvx and npx based MCP servers working together
after applying the Windows compatibility patch.

Note: The winpatch may have no effect on recent Python versions (3.8+)
that use ProactorEventLoop by default on Windows, which already supports
subprocess pipes correctly. However, it is still necessary when running
in Jupyter notebooks, which use WindowsSelectorEventLoop.
"""

import asyncio
import os
from dotenv import load_dotenv
from agents import Agent, Runner, trace, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from agents.tracing import set_trace_processors, add_trace_processor
from winpatch import winpatch_mcpserver_stdio
from custom_tracing_processor import CustomTraceProcessor

# Configuration: Toggle between OpenAI and Ollama
USE_OLLAMA = False  # Set to True to use Ollama, False for OpenAI
OLLAMA_MODEL = "qwen3:latest"  # Ollama model to use
OLLAMA_BASE_URL = "http://localhost:11434/v1"  # Ollama API base URL

if USE_OLLAMA:
    client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    MODEL = OpenAIChatCompletionsModel(model=OLLAMA_MODEL, openai_client=client)
else:
    MODEL = "gpt-4o-mini"

# Configure tracing based on model choice
# When using Ollama: Use custom local tracing to capture execution traces as JSON files
# When using OpenAI: Add custom processor alongside OpenAI's platform tracing
if USE_OLLAMA:
    set_trace_processors([CustomTraceProcessor()])  # Use only custom processor
else:
    add_trace_processor(CustomTraceProcessor())  # Add alongside OpenAI tracing


async def test_uvx_server():
    """Test uvx-based MCP server (mcp-server-fetch)."""
    print("\n" + "="*60)
    print("Testing UVX-based MCP Server (Fetch)")
    print("="*60)
    
    fetch_params = {"command": "uvx", "args": ["mcp-server-fetch"]}
    
    async with MCPServerStdio(params=fetch_params, client_session_timeout_seconds=60) as server:
        tools = await server.list_tools()
        print(f"✅ Fetch server loaded with {len(tools)} tool(s)")
        for tool in tools:
            print(f"   - {tool.name}")


async def test_npx_server():
    """Test npx-based MCP server (filesystem)."""
    print("\n" + "="*60)
    print("Testing NPX-based MCP Server (Filesystem)")
    print("="*60)
    
    sandbox_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox"))
    os.makedirs(sandbox_path, exist_ok=True)
    
    fs_params = {
        "command": "npx", 
        "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox_path]
    }
    
    async with MCPServerStdio(params=fs_params, client_session_timeout_seconds=60) as server:
        tools = await server.list_tools()
        print(f"✅ Filesystem server loaded with {len(tools)} tool(s)")
        for tool in tools:
            print(f"   - {tool.name}")


async def test_agent_with_both_servers():
    """Test an agent using both uvx and npx MCP servers together."""
    print("\n" + "="*60)
    print("Testing Agent with Both Servers")
    print("="*60)
    
    fetch_params = {"command": "uvx", "args": ["mcp-server-fetch"]}
    sandbox_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox"))
    fs_params = {
        "command": "npx", 
        "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox_path]
    }
    instructions = """
You are a specialized agent for downloading web content and saving it to files.

You have access to two tools:
1. fetch - downloads web content and returns it in the 'text' field. Always use the 'raw' parameter set to true.
2. write_file - saves text content to a file using 'path' and 'content' parameters

Always execute tools one at a time. After fetch returns, extract the text value and use it in write_file.
"""

    prompt = """
Download the webpage from https://example.com and save it to sandbox/demo_py.html

Execute step by step:
1. Use fetch to download from https://example.com
2. After fetch succeeds, use write_file to save the downloaded text to sandbox/demo_py.html
"""

    async with MCPServerStdio(params=fetch_params, client_session_timeout_seconds=60) as fetch_server:
        async with MCPServerStdio(params=fs_params, client_session_timeout_seconds=60) as fs_server:

            agent = Agent(
                name="demo_agent",
                instructions=instructions,
                model=MODEL,
                mcp_servers=[fetch_server, fs_server]
            )
            
            with trace("windows_no_wsl"):
                result = await Runner.run(
                    agent, 
                    prompt
                )
            
            print(f"✅ Agent completed task")
            print(f"   Result: {result.final_output}")
            if not USE_OLLAMA:
                print(f"\nView trace at: https://platform.openai.com/traces")


async def main():
    """Run all demonstrations."""
    load_dotenv(override=True)
    
    print("\n" + "="*60)
    print("Windows MCP Server Patch Demo")
    print("="*60)
    
    # Note: This patch may have no effect on recent Python versions (3.8+)
    # that use ProactorEventLoop by default on Windows
    winpatch_mcpserver_stdio()
    
    try:
        await test_uvx_server()
        await test_npx_server()
        await test_agent_with_both_servers()
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
