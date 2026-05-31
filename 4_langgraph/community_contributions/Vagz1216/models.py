"""
models.py — Pydantic schemas for structured LLM outputs and the LangGraph shared state.

Each schema maps directly to one agent's output. LangGraph's StateGraph uses
ResearchState as the shared whiteboard every node reads from and writes to.
"""
from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


# ── Structured output schemas ──────────────────────────────────────────────────

class SafetyCheck(BaseModel):
    is_safe: bool = Field(description="True if the query is safe and appropriate to research.")
    reason:  str  = Field(description="Brief explanation of the safety decision.")


class ClarifyingQuestions(BaseModel):
    questions:       list[str] = Field(description="Three concise clarifying questions to focus the research scope.")
    context_summary: str       = Field(description="One-sentence summary of what is already understood from the query.")


class WebSearchPlan(BaseModel):
    queries: list[str] = Field(description="Five to eight prioritised web search terms, most important first.")


class ResearchSufficiency(BaseModel):
    is_sufficient:      bool      = Field(description="True if current evidence is enough for a thorough report.")
    additional_queries: list[str] = Field(default_factory=list, description="New search terms to fill gaps.")
    reasoning:          str       = Field(description="Brief explanation of the decision.")


class ReportEvaluation(BaseModel):
    score:       float     = Field(ge=0, le=10, description="Quality score 0-10.")
    is_approved: bool      = Field(description="True if score >= 7 and report meets quality standards.")
    feedback:    str       = Field(description="Evaluation feedback.")
    suggestions: list[str] = Field(description="Actionable improvement suggestions if not approved.")


# ── LangGraph shared state ─────────────────────────────────────────────────────
# Every node receives this dict, reads what it needs, and returns a partial dict
# with only the fields it changed. LangGraph merges changes back automatically.

class ResearchState(TypedDict):
    query:                str        # original user query
    clarifying_questions: list[str]  # 3 questions from clarifier
    context_summary:      str        # one-line summary from clarifier
    user_clarification:   str        # user's selected/edited clarification
    search_plan:          list[str]  # search terms from planner
    search_results:       str        # accumulated search result text
    search_retries:       int        # extra search rounds triggered by sufficiency agent
    is_sufficient:        bool       # sufficiency verdict (read by router)
    report:               str        # markdown report from writer
    report_score:         float      # evaluator score
    report_feedback:      str        # evaluator feedback (fed back to writer on retry)
    report_retries:       int        # revision rounds triggered by evaluator
    report_approved:      bool       # evaluator verdict (read by router)
    email_status:         str        # sendgrid delivery status
