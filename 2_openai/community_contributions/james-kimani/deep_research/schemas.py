from pydantic import BaseModel, Field


class RefinedQuery(BaseModel):
    refined_query: str = Field(description="Clear, specific research question.")
    clarifications: str = Field(description="Assumptions or scope notes about the query.")


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search matters.")
    query: str = Field(description="The search term.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="List of searches to run.")


class ReportData(BaseModel):
    short_summary: str = Field(description="2-3 sentence summary.")
    markdown_report: str = Field(description="The full report in markdown.")
    follow_up_questions: list[str] = Field(description="What to research next.")


class Evaluation(BaseModel):
    is_satisfactory: bool = Field(description="Good enough to show the user?")
    feedback: str = Field(description="What's good and what's missing.")
    score: int = Field(description="Quality score, 0 to 100.")
