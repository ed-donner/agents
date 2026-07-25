

from __future__ import annotations

import os

from agents import Agent, Runner
from dotenv import load_dotenv

from mcp_params import health_triage_mcp_params, health_web_research_mcp_params

load_dotenv(override=True)

DEFAULT_MODEL = "gpt-4o-mini"
SUB_AGENT_TURNS = 5
COORDINATOR_TURNS = 20


def _intake_instructions() -> str:
    return """You are IntakeSpecialist, a structured symptom intake assistant (not a clinician).
You ONLY have access to health intake MCP tools. Use them on every substantive user message.

Workflow:
1. Call screen_for_red_flags early if the user describes symptoms.
2. Use get_intake_checklist when starting or when intake is sparse.
3. After gathering details, call record_intake_snapshot with all known fields filled.
4. When intake is reasonably complete, call full_intake_assessment with a JSON object of all fields.

Output a concise bullet summary for the coordinator: red flags, urgency tier, completeness gaps,
educational_possible_topics from tools, and exact quotes worth web follow-up (if any).
Never claim a definitive diagnosis. Repeat the tool disclaimers when tools return them."""


def _web_researcher_instructions() -> str:
    return """You are HealthWebResearcher. You have web fetch and (if configured) Brave Search plus memory MCP.

Use tools only when public, reputable information would help the user or the coordinator.
Prioritize official / high-trust sources when possible (e.g. national health agencies, major academic medical centers).
Search or fetch when:
- The user asks what X symptom might mean in general terms.
- There is travel, outbreak, medication, or vaccine context.
- Intake suggests a topic where recent public guidance exists.

Do NOT:
- Scrape paywalled clinical decision support as if it were personal medical advice.
- Contradict emergency instructions; if red flags exist, say seek emergency care first.

Return: short bullet findings, each with source title + URL if available, and a one-line limitation note.
If no search is appropriate, say why and stop."""


def _educator_instructions() -> str:
    return """You are ClinicalEducationWriter. You do NOT use tools.

Input will be a briefing from the coordinator (intake summary, tool outputs, optional web snippets).

Produce a clear, compassionate patient-facing summary with sections:
1) What we collected (facts only, no fabrication)
2) Urgency / when to seek emergency vs routine care
3) Educational context (explicitly non-diagnostic) aligned with any web sources provided
4) Suggested questions to ask a clinician
5) Disclaimer: not medical advice; not a substitute for an exam.

If the briefing indicates emergency tier, keep section 3 minimal and emphasize immediate care."""


def _coordinator_instructions(brave_configured: bool) -> str:
    search_note = (
        "HealthWebResearcher has Brave Search and fetch — delegate when public guidance helps."
        if brave_configured
        else "HealthWebResearcher has fetch only (no BRAVE_API_KEY): use for specific URLs or when user provides links; skip broad symptom googling."
    )
    return f"""You are HealthNavigator, coordinating three specialists (as tools). You are not a doctor.

Specialists:
- IntakeSpecialist: structured intake + red flags + educational pattern hints via MCP.
- HealthWebResearcher: {search_note}
- ClinicalEducationWriter: final patient-friendly write-up from the evidence you pass in.

Rules:
1. Always call IntakeSpecialist first for symptom or health-concern messages unless the user only asks for a definition and intake already done.
2. If IntakeSpecialist reports emergency urgency, tell the user to seek emergency care immediately; still call ClinicalEducationWriter only if you need a short safe summary, with minimal pathophysiology.
3. Call HealthWebResearcher when the user asks, or when reputable public info would clearly help (drug interactions overview, travel vaccines, outbreak news). Pass a focused question string.
4. Call ClinicalEducationWriter last with a single briefing string containing: user goal, intake summary, red flags, web findings (if any), and gaps.

Speak briefly to the user between tool calls when helpful. Final reply should integrate the educator output and your own judgment.
Never output a definitive diagnosis or prescription."""


async def build_health_agents(
    intake_mcp_servers: list,
    web_mcp_servers: list,
    model: str = DEFAULT_MODEL,
) -> Agent:
    brave_configured = bool(os.getenv("BRAVE_API_KEY"))

    intake_agent = Agent(
        name="IntakeSpecialist",
        instructions=_intake_instructions(),
        model=model,
        mcp_servers=intake_mcp_servers,
    )
    web_agent = Agent(
        name="HealthWebResearcher",
        instructions=_web_researcher_instructions(),
        model=model,
        mcp_servers=web_mcp_servers,
    )
    educator_agent = Agent(
        name="ClinicalEducationWriter",
        instructions=_educator_instructions(),
        model=model,
    )

    intake_tool = intake_agent.as_tool(
        tool_name="intake_specialist",
        tool_description=(
            "Structured symptom intake, red-flag screening, completeness tracking, and educational "
            "pattern hints via dedicated MCP tools. Pass the user's message and any prior context."
        ),
        max_turns=SUB_AGENT_TURNS,
    )
    web_tool = web_agent.as_tool(
        tool_name="health_web_researcher",
        tool_description=(
            "Search/fetch reputable public health information when it would help the user. "
            "Pass a focused research question; include region or year if relevant."
        ),
        max_turns=SUB_AGENT_TURNS,
    )
    educator_tool = educator_agent.as_tool(
        tool_name="clinical_education_writer",
        tool_description=(
            "Turn structured briefing into a safe, patient-facing summary with disclaimers. "
            "Call last; pass one string with intake + web findings + urgency."
        ),
        max_turns=SUB_AGENT_TURNS,
    )

    return Agent(
        name="HealthNavigator",
        instructions=_coordinator_instructions(brave_configured),
        model=model,
        tools=[intake_tool, web_tool, educator_tool],
    )


async def run_health_navigator(
    user_message: str,
    session_stem: str = "odinachi_health",
    model: str = DEFAULT_MODEL,
) -> str:
    from contextlib import AsyncExitStack

    from agents.mcp import MCPServerStdio

    async with AsyncExitStack() as stack:
        intake_srv = await stack.enter_async_context(
            MCPServerStdio(
                health_triage_mcp_params(),
                client_session_timeout_seconds=120,
                cache_tools_list=True,
            )
        )
        web_servers = []
        for params in health_web_research_mcp_params(session_stem=session_stem):
            web_servers.append(
                await stack.enter_async_context(
                    MCPServerStdio(
                        params,
                        client_session_timeout_seconds=120,
                        cache_tools_list=True,
                    )
                )
            )

        coordinator = await build_health_agents(
            intake_mcp_servers=[intake_srv],
            web_mcp_servers=web_servers,
            model=model,
        )
        result = await Runner.run(coordinator, user_message, max_turns=COORDINATOR_TURNS)
        return result.final_output or ""
