"""Shared Pydantic models and session state (plan.md Phase A)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class TriageResults(BaseModel):
    is_ambiguous: bool = Field(description="Whether the query is ambiguous")
    what_is_ambiguous: list[str] = Field(
        description="List of things that are ambiguous in the query",
    )


class ClarificationQuestions(BaseModel):
    questions: list[str] = Field(description="List of questions to clarify the query")


class SearchItem(BaseModel):
    query: str = Field(description="The search term to use")
    reason: str = Field(description="Why this search is important")


class SearchPlan(BaseModel):
    searches: list[SearchItem] = Field(description="List of web searches to perform")


class ResearchItem(BaseModel):
    query: str = Field(description="The search term to use")
    reason: str = Field(description="Why this search is important")
    result: str = Field(description="The result of the search")


class ResearchData(BaseModel):
    results: list[ResearchItem] = Field(description="Results of the web searches")


class Report(BaseModel):
    markdown_report: str = Field(description="Markdown formatted body of the report.")
    summary: str = Field(description="Summary addressing original question.")


class EvaluationResult(BaseModel):
    passes: bool = Field(description="Whether the report is acceptable.")
    gaps: list[str] = Field(
        default_factory=list,
        description="Concrete shortcomings if passes is false.",
    )
    suggested_searches: list[str] = Field(
        default_factory=list,
        description="Web search queries to improve the report if passes is false.",
    )


SessionPhase = Literal[
    "idle",
    "awaiting_clarification",
    "researching",
    "done",
    "error",
]


@dataclass
class ResearchSession:
    """Canonical question + phase + artifacts for the Gradio flow."""

    user_question: str = ""
    triage_history: list[TriageResults] = field(default_factory=list)
    pending_clarification_questions: list[str] | None = None
    phase: SessionPhase = "idle"
    last_error: str | None = None
    search_plan: SearchPlan | None = None
    research_data: ResearchData | None = None
    report: Report | None = None
    last_evaluation: EvaluationResult | None = None
    progress_log: list[str] = field(default_factory=list)
    triage_runs_completed: int = 0
    triage_complete: bool = False


def append_status_line(progress_log: list[str], message: str) -> None:
    """Append one timestamped line to the progress/status buffer (not main Markdown)."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    progress_log.append(f"[{ts}] {message}")
