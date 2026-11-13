import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from agents import Agent, ModelSettings, Runner, RunContextWrapper, function_tool
from pydantic import BaseModel, Field, model_validator

from clarifier_agent import ClarifyingQuestion, clarifier_agent
from evaluator_agent import evaluator_agent
from notify import notify
from planner_agent import MODEL_NAME, planner_agent
from search_agent import search_agent
from synthesizer_agent import synthesizer_agent
from writer_agent import REPORT_MAX_TOKENS, writer_agent

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Source:
    url: str
    title: str
    date_read: str


@dataclass
class RunContext:
    clarification_rounds: int = 0
    searches_used: int = 0
    max_searches: int = 9
    notified: bool = False
    sources: list[Source] = field(default_factory=list)
    source_numbers: dict[str, int] = field(default_factory=dict)


class ManagerTurn(BaseModel):
    status: Literal["need_answers", "final", "exhausted"]
    questions: list[ClarifyingQuestion] = Field(default_factory=list)
    report: str | None = None

    @model_validator(mode="after")
    def validate_turn(self):
        if self.status == "need_answers":
            if not 2 <= len(self.questions) <= 4:
                raise ValueError("need_answers requires between 2 and 4 questions")
            if self.report is not None:
                raise ValueError("need_answers requires report to be None")
        elif self.status == "final":
            if not self.report or not self.report.strip():
                raise ValueError("final requires a non-empty report")
            if self.questions:
                raise ValueError("final requires no questions")
        elif self.status == "exhausted":
            if not self.report or not self.report.strip():
                raise ValueError("exhausted requires a non-empty message")
            if self.questions:
                raise ValueError("exhausted requires no questions")
        return self


def _tool_error(context, error: Exception) -> str:
    return f"Tool failed: {error}"[:200]


def _extract_sources(result) -> list[Source]:
    sources = []
    seen_urls = set()
    date_read = date.today().isoformat()
    for response in getattr(result, "raw_responses", []) or []:
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) != "message":
                continue
            for content in getattr(item, "content", []) or []:
                for annotation in getattr(content, "annotations", []) or []:
                    if getattr(annotation, "type", None) != "url_citation":
                        continue
                    url = getattr(annotation, "url", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    sources.append(
                        Source(
                            url=url,
                            title=getattr(annotation, "title", "") or "",
                            date_read=date_read,
                        )
                    )
    return sources


def _register_source(context: RunContext, source: Source) -> int:
    if source.url in context.source_numbers:
        return context.source_numbers[source.url]
    context.sources.append(source)
    number = len(context.sources)
    context.source_numbers[source.url] = number
    return number


@function_tool(failure_error_function=_tool_error)
async def search_web(
    context: RunContextWrapper[RunContext], term: str, reason: str
) -> str:
    """Search the web for a term and explain why the search is needed."""
    run_context = context.context
    if run_context.searches_used >= run_context.max_searches:
        return "Search budget exhausted"

    run_context.searches_used += 1
    logger.info("search_web | term=%s | reason=%s", term, reason)
    try:
        result = await Runner.run(
            search_agent,
            f"Search term: {term}\nReason for searching: {reason}",
            context=run_context,
        )
        context.usage.add(result.context_wrapper.usage)
        sources = _extract_sources(result)
        if not sources:
            logger.warning("No URL citation annotations returned for search: %s", term)
            return str(result.final_output)
        source_numbers = [_register_source(run_context, source) for source in sources]
        numbers = ", ".join(f"[{number}]" for number in source_numbers)
        return f"{result.final_output}\n\nSources for this search: {numbers}"
    except Exception as exc:
        return f"Search failed: {exc}"[:200]


@function_tool(failure_error_function=_tool_error)
async def notify_user(context: RunContextWrapper[RunContext], text: str) -> str:
    """Send the user one notification, truncated to 1024 characters."""
    run_context = context.context
    if run_context.notified:
        return "Notification already sent"

    run_context.notified = True
    try:
        await asyncio.to_thread(notify, text[:1024])
        return "Notification sent"
    except Exception as exc:
        return f"Notification failed: {exc}"[:200]


def _role_tool(agent: Agent, name: str, description: str):
    return agent.as_tool(
        tool_name=name,
        tool_description=description,
        failure_error_function=_tool_error,
    )


MANAGER_INSTRUCTIONS = """
You manage a deep research workflow. The other agents are tools; never hand off
the conversation. Follow this required sequence: clarify only if needed, plan,
search, synthesize, write, evaluate, then notify. You must plan before searching,
run at least one search_web call before a final response, synthesize the search
results, write a report, evaluate that report, and call notify_user exactly once
with the report. Do not produce a final response if no search ran or no report
exists. If any tool returns an error, adapt and continue when possible.
Every factual claim must end with a citation [n] matching a source number from
the search results. Do not write URLs. Do not cite numbers that were not given.

Return need_answers only when clarification is essential, with two to four
questions and no report. Otherwise return final with no questions and set report
to the writer's complete markdown_report without shortening it or omitting
sections. Never return exhausted yourself; the session enforces the limit of
three accepted clarification rounds. There is a total search budget of nine
searches by default, and the current run may set a lower budget. A Search budget
exhausted response means you must stop searching and complete the workflow with
the research already available. Notifications are limited to one per session
and their text is truncated to 1024 characters.
"""

manager = Agent(
    name="Research Manager",
    instructions=MANAGER_INSTRUCTIONS,
    model=MODEL_NAME,
    model_settings=ModelSettings(max_tokens=REPORT_MAX_TOKENS),
    tools=[
        _role_tool(clarifier_agent, "clarifier", "Ask essential clarifying questions."),
        _role_tool(planner_agent, "planner", "Plan focused web searches."),
        search_web,
        _role_tool(synthesizer_agent, "synthesizer", "Review research and identify gaps."),
        _role_tool(writer_agent, "writer", "Write the cited research report."),
        _role_tool(evaluator_agent, "evaluator", "Evaluate the completed report."),
        notify_user,
    ],
    output_type=ManagerTurn,
)
