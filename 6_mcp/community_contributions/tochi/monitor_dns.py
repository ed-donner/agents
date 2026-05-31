# dns_ai_monitor_agent.py
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from pathlib import Path

# MCP Server configurations
current_dir = Path(__file__).parent
dns_server_path = str(current_dir / "dns_server.py")
push_server_path = str(current_dir / "push_server.py")

dns_server_params = {"command": "uv", "args": ["run", dns_server_path]}
push_server_params = {"command": "uv", "args": ["run", push_server_path]}

load_dotenv(override=True)

instructions = """You are a DNS expiry monitoring assistant. Your job is to:
1. Check domains expiring within 3 months
2. Prioritize domains by urgency (7 days = critical, 30 days = warning, 90 days = notice)
3. Send concise, actionable push notifications
4. Format notifications to be clear and urgent when needed

When sending notifications:
- Keep messages under 250 characters
- Include: domain name, days left, and action needed
- Use appropriate urgency indicators
- Be concise but informative
"""


async def run_dns_monitor_agent():
    """Run intelligent DNS monitoring agent"""
    
    async with MCPServerStdio(params=dns_server_params, client_session_timeout_seconds=30) as dns_server:
        async with MCPServerStdio(params=push_server_params, client_session_timeout_seconds=30) as push_server:
            
            agent = Agent(
                name="dns_monitor",
                instructions=instructions,
                model="gpt-4o-mini",
                mcp_servers=[dns_server, push_server]
            )
            
            print("🤖 Starting DNS Monitoring Agent...\n")
            
            # Run the agent with the monitoring task
            result = await Runner.run(
                agent, 
                "Check all domains expiring within 3 months and send push notifications for each one based on urgency. Prioritize critical domains (< 7 days) first."
            )
            
            print(f"\n✅ Agent Summary:\n{result.final_output}\n")


async def main():
    await run_dns_monitor_agent()


if __name__ == "__main__":
    asyncio.run(main())