import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, WebSearchTool, function_tool, set_default_openai_api, set_default_openai_client
from agents.model_settings import ModelSettings

from schemas import (
    ClarificationDecision,
    GuardrailDecision,
    ResearchPlan,
    ResearchReport,
    SearchFinding,
)

load_dotenv(override=True)

MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
BASE_URL = "https://openrouter.ai/api/v1"
TODAY = datetime.now().strftime("%B %d, %Y")
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
set_default_openai_client(client, use_for_tracing=False)
set_default_openai_api("chat_completions")


def save_report_file(title: str, markdown: str) -> Dict[str, str]:
    safe_title = "".join(c.lower() if c.isalnum() else "_" for c in title).strip("_")
    path = OUTPUT_DIR / f"{safe_title[:80] or 'research_report'}.md"
    path.write_text(markdown, encoding="utf-8")
    return {"status": "saved", "path": str(path)}


def save_research_note_file(note: str) -> Dict[str, str]:
    path = OUTPUT_DIR / "research_notes.txt"
    with path.open("a", encoding="utf-8") as f:
        f.write(note + "\n")
    return {"status": "saved", "path": str(path)}


@function_tool
def save_report(title: str, markdown: str) -> Dict[str, str]:
    """Save a markdown report to a local file."""
    return save_report_file(title, markdown)


@function_tool
def save_research_note(note: str) -> Dict[str, str]:
    """Save a small run note for debugging or audit trail."""
    return save_research_note_file(note)


guardrail_agent = Agent(
    name="GuardrailAgent",
    instructions=(
        "You are a safety and scope guardrail for a research assistant. "
        "Allow normal public-topic research. Block requests involving doxxing, stalking, "
        "private personal data gathering, targeted harassment, malware, or clearly harmful wrongdoing. "
        "Return a concise decision. "
        f"Today's date is {TODAY}."
    ),
    model=MODEL,
    output_type=GuardrailDecision,
)

clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=(
        "You decide whether a research query is too broad or ambiguous. "
        "Ask clarifying questions when needed, especially around scope, audience, time frame, geography, "
        "and desired output style. If the query is already clear enough, set needs_clarification to false "
        "and provide a few reasonable assumptions. "
        f"Today's date is {TODAY}. Prefer clarifications that help make the research current and time-bounded when relevant."
    ),
    model=MODEL,
    output_type=ClarificationDecision,
)

planner_agent = Agent(
    name="PlannerAgent",
    instructions=(
        "You are a research planner. Given the original query and any clarifications, produce a focused "
        "research objective, a search plan, and a report angle. Prioritize high-signal searches. "
        f"Today's date is {TODAY}. Prefer searches that surface the most current information available."
    ),
    model=MODEL,
    output_type=ResearchPlan,
)

search_agent = Agent(
    name="SearchAgent",
    instructions=(
        "You are a research search specialist. Use web search to gather high-value information for the given "
        "query. Summarize findings concisely and include key sources or domains that informed the summary. "
        f"Today's date is {TODAY}. Prioritize recent and date-specific information whenever possible."
    ),
    model=MODEL,
    tools=[WebSearchTool(search_context_size="medium")],
    model_settings=ModelSettings(tool_choice="required"),
    output_type=SearchFinding,
)

writer_agent = Agent(
    name="WriterAgent",
    instructions=(
        "You are a senior research writer. Given a research objective, clarifications, and search findings, "
        "produce a high-quality markdown report with a clear executive summary, structured sections, "
        "and suggested follow-up questions. "
        f"Today's date is {TODAY}. Make the report explicitly current as of today, and mention exact dates when recency matters."
    ),
    model=MODEL,
    tools=[save_report, save_research_note],
    output_type=ResearchReport,
)


class ClarifyingDeepResearcher:
    def __init__(self):
        self.guardrail_agent = guardrail_agent
        self.clarifier_agent = clarifier_agent
        self.planner_agent = planner_agent
        self.search_agent = search_agent
        self.writer_agent = writer_agent

    async def check_guardrails(self, query: str) -> GuardrailDecision:
        result = await Runner.run(self.guardrail_agent, f"Research request: {query}")
        return result.final_output_as(GuardrailDecision)

    async def clarify(self, query: str) -> ClarificationDecision:
        result = await Runner.run(self.clarifier_agent, f"User query: {query}")
        return result.final_output_as(ClarificationDecision)

    async def plan(self, query: str, clarification_answers: str) -> ResearchPlan:
        prompt = (
            f"Original query: {query}\n"
            f"Clarifications / assumptions: {clarification_answers}\n"
        )
        result = await Runner.run(self.planner_agent, prompt)
        return result.final_output_as(ResearchPlan)

    async def run_one_search(self, query: str, reason: str) -> SearchFinding | None:
        prompt = f"Search query: {query}\nWhy this search matters: {reason}"
        try:
            result = await Runner.run(self.search_agent, prompt)
            return result.final_output_as(SearchFinding)
        except Exception:
            return None

    async def search(self, plan: ResearchPlan) -> List[SearchFinding]:
        tasks = [
            asyncio.create_task(self.run_one_search(item.query, item.reason))
            for item in plan.searches
        ]
        findings: List[SearchFinding] = []
        for task in asyncio.as_completed(tasks):
            finding = await task
            if finding is not None:
                findings.append(finding)
        return findings

    async def write_report(
        self,
        query: str,
        clarification_answers: str,
        plan: ResearchPlan,
        findings: List[SearchFinding],
    ) -> ResearchReport:
        prompt = (
            f"Original query: {query}\n\n"
            f"Clarifications / assumptions: {clarification_answers}\n\n"
            f"Research objective: {plan.objective}\n"
            f"Report angle: {plan.report_angle}\n\n"
            f"Findings:\n{findings}"
        )
        result = await Runner.run(self.writer_agent, prompt)
        return result.final_output_as(ResearchReport)

    async def analyze_query(self, query: str) -> Dict:
        guardrail = await self.check_guardrails(query)
        if not guardrail.allowed:
            return {
                "status": "blocked",
                "guardrail": guardrail,
                "clarification": None,
            }

        clarification = await self.clarify(query)
        return {
            "status": "ready",
            "guardrail": guardrail,
            "clarification": clarification,
        }

    async def run_full_research(self, query: str, clarification_answers: str) -> Dict:
        guardrail = await self.check_guardrails(query)
        if not guardrail.allowed:
            return {
                "status": "blocked",
                "guardrail": guardrail,
            }

        plan = await self.plan(query, clarification_answers)
        findings = await self.search(plan)
        report = await self.write_report(query, clarification_answers, plan, findings)
        saved_report = save_report_file(query, report.markdown_report)
        save_research_note_file(f"Completed research run for: {query}")

        return {
            "status": "completed",
            "guardrail": guardrail,
            "plan": plan,
            "findings": findings,
            "report": report,
            "saved_report": saved_report,
        }
