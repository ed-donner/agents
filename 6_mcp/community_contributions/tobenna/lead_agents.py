from contextlib import AsyncExitStack
from dataclasses import dataclass
from pathlib import Path

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from leads import Lead
from lead_templates import (
    build_manager_prompt,
    intake_agent_instructions,
    intake_tool_description,
    notification_agent_instructions,
    notification_tool_description,
    orchestration_agent_instructions,
    qualification_agent_instructions,
    qualification_tool_description,
    routing_agent_instructions,
    routing_tool_description,
)

MODEL_NAME = "gpt-4o-mini"
MAX_TURNS = 12
ORCHESTRATOR_MAX_TURNS = 24
LEAD_SERVER_PATH = Path(__file__).resolve().parent / "leads_server.py"
PUSH_SERVER_PATH = Path(__file__).resolve().parent / "push_server.py"


@dataclass
class LeadDeskResult:
    summary: str
    lead_id: str


class LeadDeskCoordinator:
    def _resolve_created_lead(self, known_ids: set[str]) -> Lead:
        leads = Lead.list()
        if not leads:
            raise RuntimeError("Intake stage completed without a saved lead")
        return next((lead for lead in leads if lead.id not in known_ids), leads[0])

    def _build_stage_agent(
        self,
        name: str,
        instructions: str,
        servers: list[MCPServerStdio],
    ) -> Agent:
        return Agent(
            name=name,
            instructions=instructions,
            model=MODEL_NAME,
            mcp_servers=servers,
        )

    async def _create_orchestrator_agent(
        self,
        lead_server: MCPServerStdio,
        push_server: MCPServerStdio,
    ) -> Agent:
        intake_agent = self._build_stage_agent(
            name="LeadIntakeAgent",
            instructions=intake_agent_instructions(),
            servers=[lead_server],
        )
        qualification_agent = self._build_stage_agent(
            name="LeadQualificationAgent",
            instructions=qualification_agent_instructions(),
            servers=[lead_server],
        )
        routing_agent = self._build_stage_agent(
            name="LeadRoutingAgent",
            instructions=routing_agent_instructions(),
            servers=[lead_server],
        )
        notification_agent = self._build_stage_agent(
            name="LeadNotificationAgent",
            instructions=notification_agent_instructions(),
            servers=[lead_server, push_server],
        )

        return Agent(
            name="LeadDeskOrchestrator",
            instructions=orchestration_agent_instructions(),
            model=MODEL_NAME,
            tools=[
                intake_agent.as_tool(
                    tool_name="process_lead_intake",
                    tool_description=intake_tool_description(),
                    max_turns=MAX_TURNS,
                ),
                qualification_agent.as_tool(
                    tool_name="qualify_saved_lead",
                    tool_description=qualification_tool_description(),
                    max_turns=MAX_TURNS,
                ),
                routing_agent.as_tool(
                    tool_name="route_saved_lead",
                    tool_description=routing_tool_description(),
                    max_turns=MAX_TURNS,
                ),
                notification_agent.as_tool(
                    tool_name="notify_saved_lead",
                    tool_description=notification_tool_description(),
                    max_turns=MAX_TURNS,
                ),
            ],
        )

    async def process_new_lead(
        self,
        freeform_brief: str,
        name: str,
        email: str,
        company: str,
        role_title: str,
        interest: str,
    ) -> LeadDeskResult:
        known_ids = {lead.id for lead in Lead.list()}
        async with AsyncExitStack() as stack:
            lead_server = await stack.enter_async_context(
                MCPServerStdio(
                    {"command": "uv", "args": ["run", str(LEAD_SERVER_PATH)]},
                    client_session_timeout_seconds=120,
                )
            )
            push_server = await stack.enter_async_context(
                MCPServerStdio(
                    {"command": "uv", "args": ["run", str(PUSH_SERVER_PATH)]},
                    client_session_timeout_seconds=120,
                )
            )

            orchestrator = await self._create_orchestrator_agent(lead_server, push_server)
            result = await Runner.run(
                orchestrator,
                build_manager_prompt(freeform_brief, name, email, company, role_title, interest),
                max_turns=ORCHESTRATOR_MAX_TURNS,
            )

            latest_lead = self._resolve_created_lead(known_ids)

            final_lead = Lead.get(latest_lead.id)
            workflow_summary = "\n\n".join(
                [
                    result.final_output,
                    "## Persisted Lead State",
                    f"- Lead ID: {final_lead.id}",
                    f"- Status: {final_lead.status}",
                    f"- Qualification: {final_lead.qualification_status} ({final_lead.priority})",
                    f"- Route: {final_lead.routing_owner or 'unassigned'} / {final_lead.routing_queue or 'unassigned'}",
                    f"- Notification: {final_lead.notification_status}",
                ]
            )
            return LeadDeskResult(summary=workflow_summary, lead_id=final_lead.id)