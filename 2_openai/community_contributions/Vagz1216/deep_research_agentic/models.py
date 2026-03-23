from __future__ import annotations
from pydantic import BaseModel, Field


class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(
        description="Three concise clarifying questions to sharpen the research scope."
    )
    context_summary: str = Field(
        description="One-sentence summary of what is already understood from the query."
    )


class WebSearchItem(BaseModel):
    query: str = Field(description="The search term to use.")
    reason: str = Field(description="Why this search is relevant to the overall query.")
    priority: int = Field(
        description="Priority 1 (critical) to 3 (nice-to-have).", ge=1, le=3
    )


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="Ordered list of web searches to perform."
    )


class ResearchSufficiencyCheck(BaseModel):
    is_sufficient: bool = Field(
        description="True if current results are enough for a thorough report."
    )
    missing_aspects: list[str] = Field(
        description="Topics or angles still not covered."
    )
    additional_queries: list[str] = Field(
        description="New search queries to fill the gaps, empty if sufficient."
    )
    reasoning: str = Field(description="Brief explanation of the decision.")


class ReportData(BaseModel):
    short_summary: str = Field(description="2-3 sentence executive summary.")
    markdown_report: str = Field(description="Full detailed report in Markdown (≥1000 words).")
    follow_up_questions: list[str] = Field(description="Suggested directions for further research.")


class ReportEvaluation(BaseModel):
    is_approved: bool = Field(description="True if the report meets quality standards.")
    score: float = Field(description="Quality score 0–10.", ge=0, le=10)
    strengths: list[str] = Field(description="What the report does well.")
    weaknesses: list[str] = Field(description="Areas that fall short.")
    improvement_suggestions: list[str] = Field(
        description="Actionable suggestions; empty if approved."
    )
