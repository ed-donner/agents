import json
from datetime import datetime
from contextlib import AsyncExitStack
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from .simple_database import update_agent_status
from .tracers import make_trace_id
from .config import config
from .email_agent import email_agent


class AlertManager:
    def __init__(self):
        self.name = "AlertManager"
        self.model_name = config.MODEL_NAME
        self.max_turns = config.MAX_TURNS_ALERT
        self.mcp_timeout = config.MCP_TIMEOUT
        self.agent = None
        
    async def create_agent(self, mcp_servers) -> Agent:
        instructions = """You are an Alert Manager Agent for a DevOps operations center.

Your job is to:
1. Check for active alerts using get_system_alerts()
2. Review alert priority and severity levels
3. Resolve alerts that are no longer relevant using resolve_system_alert()
4. Provide alert summaries and recommendations

Always start by getting current active alerts.
For alerts that seem resolved (like temporary CPU spikes), you can resolve them.
Provide clear summaries of alert status and any actions taken.

Note: Email notifications are handled separately by the email agent."""
        self.agent = Agent(
            name=self.name,
            instructions=instructions,
            model=self.model_name,
            mcp_servers=mcp_servers
        )
        return self.agent

    async def send_email_for_critical_alerts(self, alerts):
        critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
        if not critical_alerts:
            return None
        alert_text = f"CRITICAL DEVOPS ALERTS - {len(critical_alerts)} Critical Issue(s) Detected\n\n"
        alert_text += "Please format these alerts into a professional HTML email:\n\n"
        for i, alert in enumerate(critical_alerts, 1):
            alert_text += f"Alert #{i}:\n"
            alert_text += f"  Title: {alert['title']}\n"
            alert_text += f"  Severity: {alert['severity'].upper()}\n"
            alert_text += f"  Message: {alert['message']}\n"
            alert_text += f"  Created: {alert['created_at']}\n"
            if alert.get('metadata'):
                metadata = alert['metadata']
                if isinstance(metadata, dict):
                    alert_text += "  Metrics:\n"
                    for key, value in metadata.items():
                        readable_key = key.replace('_', ' ').title()
                        if isinstance(value, (int, float)):
                            alert_text += f"    {readable_key}: {value:.1f}%\n"
                        else:
                            alert_text += f"    {readable_key}: {value}\n"
            alert_text += "\n"
        alert_text += "Recommendations:\n"
        alert_text += "- Investigate and resolve high resource usage immediately\n"
        alert_text += "- Check for runaway processes or memory leaks\n"
        alert_text += "- Consider scaling resources if the issue persists\n"
        alert_text += "- Monitor system metrics closely\n"
        result = await Runner.run(email_agent, alert_text)
        return result

    async def run_alert_cycle(self, mcp_servers):
        try:
            agent = await self.create_agent(mcp_servers)
            message = "Check current alerts and manage them. Resolve any alerts that are no longer relevant."
            result = await Runner.run(agent, message, max_turns=self.max_turns)
            from .simple_database import get_active_alerts
            alerts = get_active_alerts()
            if alerts:
                await self.send_email_for_critical_alerts(alerts)
            update_agent_status(self.name.lower(), "completed")
            return result.final_output
        except Exception as e:
            error_msg = f"Error in alert cycle: {str(e)}"
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
            return await self.run_alert_cycle([mcp_server])

    async def run_with_trace(self):
        from agents import trace
        trace_name = f"alert-manager-cycle"
        trace_id = make_trace_id("alertmanager")
        with trace(trace_name, trace_id=trace_id):
            return await self.run_with_mcp_server()

    async def run(self):
        try:
            update_agent_status(self.name.lower(), "running")
            result = await self.run_with_trace()
            return result
        except Exception as e:
            error_msg = f"Error running Alert Manager: {str(e)}"
            update_agent_status(self.name.lower(), "error", error_msg)
            raise