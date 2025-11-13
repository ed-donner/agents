import asyncio
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from agents import Agent, Runner
from pathlib import Path

load_dotenv(override=True)

# MCP Server configuration - use absolute path
current_dir = Path(__file__).parent
dns_server_path = str(current_dir / "dns_server.py")
params = {"command": "uv", "args": ["run", dns_server_path]}

instructions = """You are a DNS lookup specialist. You can help users get information about domain names.

IMPORTANT: When you lookup any domain information, ALWAYS use the 'lookup_and_save_domain' tool to both get the info AND save it to the database.

You can help with:
- Domain registrar information
- Domain creation dates  
- Domain expiration dates
- Name servers
- Monitoring domains expiring soon (use watch_dns)
- Viewing all tracked domains (use get_all_tracked_domains)

Always confirm when a domain has been saved to the tracking database."""


def dns_chat(message, history):
    """Chat function - must return only a string"""
    
    async def get_response():
        try:
            async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
                agent = Agent(
                    name="dns_specialist",
                    instructions=instructions,
                    model="gpt-4o-mini",
                    mcp_servers=[mcp_server]
                )
                
                # Run agent
                result = await Runner.run(agent, message)
                
                # Return only the text
                return result.final_output
                
        except Exception as e:
            error_msg = f"❌ **Error**: {str(e)}\n\n"
            return error_msg
    
    return asyncio.run(get_response())