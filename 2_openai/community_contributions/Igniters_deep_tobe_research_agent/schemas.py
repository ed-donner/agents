from pydantic import BaseModel, Field


class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(
        description="Exactly three clarifying questions to sharpen the research request.",
        min_length=3,
        max_length=3,
    )


class WebSearchItem(BaseModel):
    query: str = Field(description="A focused web search query.")
    reason: str = Field(description="Why this search matters for the current round.")


class WebSearchPlan(BaseModel):
    round_number: int = Field(description="The research round this plan is for.")
    round_goal: str = Field(description="The main objective for the current research round.")
    searches: list[WebSearchItem] = Field(
        description="A targeted set of searches for this round.",
        min_length=2,
        max_length=5,
    )


class SearchEvidence(BaseModel):
    search_query: str = Field(description="The search query that was executed.")
    reason: str = Field(description="Why the search was executed.")
    summary: str = Field(description="A concise synthesis of the evidence gathered.")
    key_findings: list[str] = Field(
        description="Concrete findings from this search.",
        default_factory=list,
    )
    sources: list[str] = Field(
        description="Source URLs consulted for this search.",
        default_factory=list,
    )


class CoverageAssessment(BaseModel):
    is_complete: bool = Field(
        description="Whether the accumulated evidence is sufficient for the final report."
    )
    coverage_summary: str = Field(
        description="A concise assessment of how well the research covers the query."
    )
    gaps: list[str] = Field(
        description="Specific remaining gaps, if any.",
        default_factory=list,
    )
    next_round_focus: str = Field(
        description="Guidance for the next round if coverage is incomplete.",
        default="",
    )


class ReportData(BaseModel):
    executive_summary: str = Field(
        description="A short executive summary of the overall findings."
    )
    markdown_report: str = Field(description="The final markdown research report.")
    follow_up_questions: list[str] = Field(
        description="Suggested follow-up questions the user could explore next.",
        default_factory=list,
    )
