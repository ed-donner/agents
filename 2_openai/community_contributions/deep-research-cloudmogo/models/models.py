from pydantic import BaseModel, Field

# pydantic model for WebSearchItem and WebSearchPlan

class Clarification(BaseModel):
    clarification_questions:list[str] = Field (description="This represents/holds a clarification Question")
    clarification_answers:list[str] = Field(default_factory=list)

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning why this search is important to the query.")
    query: str = Field (description="The search term to use for web search.")

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field (description="A List of the web searches to perform to best answer the query.")


class ReportData(BaseModel):
    short_summary: str = Field (description="A short 2-3 sentence summary of the findings.")

    markdown_report: str = Field (description="The final report")

    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Suggested topics to research further",
    )


class SearchEvidence(BaseModel):
    query: str = Field(description="The web search query that was executed.")
    reason: str = Field(description="Why this search mattered to the overall task.")
    summary: str = Field(description="The concise result summary produced by the search agent.")
    source_urls: list[str] = Field(
        default_factory=list,
        description="Source URLs or citations collected during the search.",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Known gaps, ambiguities, or unanswered questions after the search.",
    )


class ResearchState(BaseModel):
    original_query: str = Field(description="The user research request.")
    clarification: Clarification | None = Field(
        default=None,
        description="Clarification questions and answers gathered from the user.",
    )
    planned_searches: list[WebSearchItem] = Field(
        default_factory=list,
        description="Searches the system currently plans to run.",
    )
    evidence: list[SearchEvidence] = Field(
        default_factory=list,
        description="Accumulated evidence gathered from searches.",
    )
    report: ReportData | None = Field(
        default=None,
        description="The current draft or final report.",
    )
    next_action: str | None = Field(
        default=None,
        description="The next best action the supervisor believes should happen.",
    )
    needs_clarification: bool = Field(
        default=False,
        description="Whether the supervisor believes more user clarification is required.",
    )
    ready_to_email: bool = Field(
        default=False,
        description="Whether the report is complete and approved for email delivery.",
    )
    delivery_status: str | None = Field(
        default=None,
        description="Status of any delivery action such as sending an email.",
    )


class ResearchUIState(BaseModel):
    clarification: Clarification = Field(
        default_factory=lambda: Clarification(
            clarification_questions=[],
            clarification_answers=[],
        ),
        description="Clarification state currently shown in the UI.",
    )
    show_submit: bool = Field(
        default=False,
        description="Whether the submit-answers button should be visible.",
    )
    show_output: bool = Field(
        default=False,
        description="Whether the output area should be visible.",
    )


class AppState(BaseModel):
    query: str = Field(
        default="",
        description="The current user query in the app.",
    )
    ui: ResearchUIState = Field(
        default_factory=ResearchUIState,
        description="The current UI state for the app.",
    )
    research: ResearchState | None = Field(
        default=None,
        description="The most recent research state returned by the supervisor.",
    )
