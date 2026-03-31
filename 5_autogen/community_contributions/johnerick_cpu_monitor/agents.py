import os
import requests
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.langchain import LangChainToolAdapter
from langchain_community.tools import ShellTool
from dotenv import load_dotenv
import json
import re

from messages import MonitorRequest, MetricsReport, TriageReport, FixerRequest, IncidentResult

load_dotenv(override=True)

runtime = None

shell_tool = LangChainToolAdapter(ShellTool(ask_human_input=False))


def patch_config_tool(filepath: str, find: str, replace: str) -> str:

    if not os.path.exists(filepath):
        return f"ERROR: {filepath} does not exist"
    with open(filepath, "r") as f:
        content = f.read()
    if find not in content:
        return f"WARNING: '{find}' not found in {filepath}"
    content = content.replace(find, replace)
    with open(filepath, "w") as f:
        f.write(content)
    return f"Patched {filepath}: replaced '{find}' with '{replace}'"


def restart_service_tool(service_name: str) -> str:
    """Simulates restarting a service - no real systemctl"""
    return f"Service '{service_name}' restarted successfully (simulated)"


def write_incident_log_tool(severity: str, summary: str, action: str, outcome: str) -> str:
    os.makedirs("logs", exist_ok=True)
    from datetime import datetime
    entry = (
        f"[{datetime.now().isoformat()}] SEVERITY={severity}\n"
        f"  Summary : {summary}\n"
        f"  Action  : {action}\n"
        f"  Outcome : {outcome}\n"
        f"{'─'*60}\n"
    )
    with open("logs/incidents.log", "a") as f:
        f.write(entry)
    return f"Logged to logs/incidents.log"


def pushover_notify_tool(title: str, message: str) -> str:
    user_key  = os.getenv("PUSHOVER_USER_KEY")
    api_token = os.getenv("PUSHOVER_API_TOKEN")
    if not user_key or not api_token:
        return "SKIP: PUSHOVER_USER_KEY or PUSHOVER_API_TOKEN not set in .env"
    resp = requests.post("https://api.pushover.net/1/json", data={
        "token":   api_token,
        "user":    user_key,
        "title":   title,
        "message": message,
        "priority": 1,  
    })
    return "Pushover sent" if resp.status_code == 200 else f"Pushover failed: {resp.text}"


def make_client(temperature: float = 0.3) -> OpenAIChatCompletionClient:
    return OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=temperature)

class MonitoringAgent(RoutedAgent):
    system_message = """
    You are a server monitoring agent. Use the shell tool to run these commands
    and return the raw combined output:
      - df -h       (disk usage)
      - uptime      (CPU load)
      - tail -n 20 /var/log/syslog 2>/dev/null || echo "syslog unavailable"
    Return only the raw output, no commentary.
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._delegate = AssistantAgent(
            name,
            model_client=make_client(),
            system_message=self.system_message,
            tools=[shell_tool],
        )

    @message_handler
    async def handle_message(
        self, message: MonitorRequest, ctx: MessageContext
    ) -> MetricsReport:
        print("[MonitoringAgent] Running system checks...")
        response = await self._delegate.on_messages(
            [TextMessage(content="Run the monitoring checks now.", source="user")],
            ctx.cancellation_token,
        )
        return MetricsReport(raw_output=response.chat_message.content)


class TriageAgent(RoutedAgent):
    system_message = """
    You are a DevOps triage agent. You receive raw server metrics and logs.
    Analyse them and respond with ONLY a JSON object in this exact format:
    {
      "severity": "low|medium|high|critical",
      "summary": "one sentence describing the issue",
      "suggested_action": "one concrete action to fix it"
    }

    Severity rules:
    - low: everything normal
    - medium: disk > 70% or load average > 2.0
    - high: disk > 85% or load average > 4.0 or suspicious log entries
    - critical: disk > 95% or load average > 8.0 or clear error patterns in logs
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._delegate = AssistantAgent(
            name,
            model_client=make_client(temperature=0.1),
            system_message=self.system_message,
        )

    @message_handler
    async def handle_message(
        self, message: MetricsReport, ctx: MessageContext
    ) -> TriageReport:
        print("[TriageAgent]    Analysing metrics...")
        response = await self._delegate.on_messages(
            [TextMessage(content=message.raw_output, source="user")],
            ctx.cancellation_token,
        )
        content = response.chat_message.content
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            data = json.loads(match.group()) if match else {}

        severity         = data.get("severity", "low")
        summary          = data.get("summary", content)
        suggested_action = data.get("suggested_action", "Monitor and observe")

        print(f"[TriageAgent]    Severity: {severity.upper()} — {summary}")
        return TriageReport(
            raw_output=message.raw_output,
            severity=severity,
            summary=summary,
            suggested_action=suggested_action,
        )


class HumanProxyAgent(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    @message_handler
    async def handle_message(
        self, message: FixerRequest, ctx: MessageContext
    ) -> FixerRequest:
        t = message.triage
        print(f"\n{'!'*60}")
        print(f"  HUMAN APPROVAL REQUIRED")
        print(f"  Severity : {t.severity.upper()}")
        print(f"  Issue    : {t.summary}")
        print(f"  Action   : {t.suggested_action}")
        print(f"{'!'*60}")

        pushover_notify_tool(
            title=f"[CRITICAL] Server incident",
            message=f"{t.summary}\nProposed fix: {t.suggested_action}",
        )

        answer = input("\nApprove this action? (yes/no): ").strip().lower()
        approved = answer == "yes"
        print(f"[HumanProxy]     {'Approved' if approved else 'Rejected'} by operator\n")
        return FixerRequest(triage=message.triage, approved=approved)


class FixerAgent(RoutedAgent):
    system_message = """
    You are a DevOps fixer agent. You receive an approved incident report and must
    take action using the available tools. Choose the most appropriate tool:
    - Use restart_service_tool if a service needs restarting
    - Use patch_config_tool if a config value needs changing
    - Use write_incident_log_tool to always log what you did
    Respond with a brief sentence describing what you did.
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._delegate = AssistantAgent(
            name,
            model_client=make_client(temperature=0.2),
            system_message=self.system_message,
            tools=[restart_service_tool, patch_config_tool, write_incident_log_tool],
        )

    @message_handler
    async def handle_message(
        self, message: FixerRequest, ctx: MessageContext
    ) -> IncidentResult:
        t = message.triage

        if not message.approved:
            write_incident_log_tool(t.severity, t.summary, "rejected by operator", "no action taken")
            print("[FixerAgent]     Action rejected — logged and skipping.")
            return IncidentResult(
                severity=t.severity,
                action_taken="none — rejected by operator",
                outcome="no change",
            )

        print(f"[FixerAgent]     Applying fix: {t.suggested_action}")
        prompt = (
            f"Incident: {t.summary}\n"
            f"Suggested action: {t.suggested_action}\n"
            f"Severity: {t.severity}\n\n"
            "Use the tools to fix this and log the incident."
        )
        response = await self._delegate.on_messages(
            [TextMessage(content=prompt, source="user")],
            ctx.cancellation_token,
        )
        outcome = response.chat_message.content
        print(f"[FixerAgent]     {outcome}")
        return IncidentResult(
            severity=t.severity,
            action_taken=t.suggested_action,
            outcome=outcome,
        )


class OrchestratorAgent(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    @message_handler
    async def handle_message(
        self, message: MonitorRequest, ctx: MessageContext
    ) -> IncidentResult:
        metrics: MetricsReport = await runtime.send_message(
            message, AgentId("monitoring_agent", "default")
        )
        triage: TriageReport = await runtime.send_message(
            metrics, AgentId("triage_agent", "default")
        )

        fixer_request = FixerRequest(triage=triage)

        if triage.severity == "critical":
            fixer_request = await runtime.send_message(
                fixer_request, AgentId("human_proxy_agent", "default")
            )
        else:
            fixer_request.approved = True  

        result: IncidentResult = await runtime.send_message(
            fixer_request, AgentId("fixer_agent", "default")
        )
        return result