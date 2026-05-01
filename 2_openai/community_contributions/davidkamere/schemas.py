from pydantic import BaseModel, Field
from typing import List

#guardrails
class GuardrailDecision(BaseModel):
    allowed: bool = Field(description="Whether the research request is allowed to proceed.")
    reason: str = Field(description="Short explanation of why the request is allowed or blocked.")


class ClarifyingQuestion(BaseModel):
    question: str = Field(description="A clarifying question that would help narrow the research task.")
    reason: str = Field(description="Why this clarification is important.")

class ClarificationDecision(BaseModel):
    needs_clarification: bool = Field(description="Whether the original query is too broad or ambiguous.")
    questions: List[ClarifyingQuestion] = Field(
        default_factory=list,
        description="Clarifying questions to ask before research starts."
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Reasonable assumptions if no clarification is needed."
    )

class SearchItem(BaseModel):
    query: str = Field(description="The search query to run.")
    reason: str = Field(description="Why this search is useful.")
    priority: int = Field(description="Priority of the search from 1 to 5.")


class ResearchPlan(BaseModel):
    objective: str = Field(description="The final interpreted research objective.")
    searches: List[SearchItem] = Field(description="List of searches to perform.")
    report_angle: str = Field(description="Recommended framing for the final report.")


class SearchFinding(BaseModel):
    query: str = Field(description="The search query that produced this finding.")
    summary: str = Field(description="Concise summary of the findings from this search.")
    key_sources: List[str] = Field(
        default_factory=list,
        description="Important sources or domains that informed the summary."
    )

class ResearchReport(BaseModel):
    executive_summary: str = Field(description="Short executive summary of the research.")
    markdown_report: str = Field(description="Full report in markdown format.")
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions for deeper research."
    )