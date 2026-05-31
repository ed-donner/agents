from datetime import datetime
from contextlib import AsyncExitStack
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from .simple_database import update_agent_status
from .tracers import make_trace_id
from .config import config


class SystemMonitor:
    def __init__(self):
        self.name = "SystemMonitor"
        self.model_name = config.MODEL_NAME
        self.max_turns = config.MAX_TURNS_MONITOR
        self.mcp_timeout = config.MCP_TIMEOUT
        self.agent = None

    async def create_agent(self, mcp_servers) -> Agent:
        instructions = """You are a System Monitor Agent for a DevOps operations center.

Your job is to:
1. Check system health using get_system_metrics()
2. Run health checks using check_system_health()
3. Monitor for issues and create alerts if needed
4. Provide clear status reports

Always start by getting current system metrics, then run a health check.
If any metrics are concerning (>80% for CPU/memory, >85% for disk), mention this clearly.
Be concise but informative in your reports."""
        self.agent = Agent(
            name=self.name,
            instructions=instructions,
            model=self.model_name,
            mcp_servers=mcp_servers
        )
        return self.agent

    async def run_monitoring_cycle(self, mcp_servers):
        try:
            agent = await self.create_agent(mcp_servers)
            message = "Check the current system status and health. Report on any issues found."
            result = await Runner.run(agent, message, max_turns=self.max_turns)
            update_agent_status(self.name.lower(), "completed")
            return result.final_output
        except Exception as e:
            error_msg = f"Error in monitoring cycle: {str(e)}"
            update_agent_status(self.name.lower(), "error", error_msg)
            raise

    async def run_with_mcp_server(self):
        server_params = {
            "command": "python",
            "args": ["-m", "src.devops_server"],
            "env": {}
        }
        async with AsyncExitStack() as stack:
            mcp_server = await stack.enter_async_context(
                MCPServerStdio(server_params, client_session_timeout_seconds=self.mcp_timeout)
            )
            return await self.run_monitoring_cycle([mcp_server])

    async def run_with_trace(self):
        from agents import trace
        trace_name = f"system-monitor-cycle"
        trace_id = make_trace_id("systemmonitor")
        with trace(trace_name, trace_id=trace_id):
            return await self.run_with_mcp_server()

    async def run(self):
        try:
            update_agent_status(self.name.lower(), "running")
            result = await self.run_with_trace()
            return result
        except Exception as e:
            error_msg = f"Error running System Monitor: {str(e)}"
            update_agent_status(self.name.lower(), "error", error_msg)
            raise