from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str = Field(description="The title of the search result.")
    link: str = Field(description="The URL of the search result.")
    content: str = Field(description="The content snippet of the search result.")


class SearchResults(BaseModel):
    results: list[SearchResult] = Field(description="A list of search results.")


class WebSearchItem(BaseModel):
    reason: str = Field(
        description="Your reasoning for why this search is important to the query."
    )
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


class SyllabusData(BaseModel):
    short_summary: str = Field(description="A short summary of the syllabus.")
    markdown_report: str = Field(
        description="The full syllabus report in markdown format."
    )
    follow_up_questions: list[str] = Field(
        description="A list of follow-up questions related to the syllabus."
    )


class TopicCheckOutput(BaseModel):
    """
    The structured output from our topic-checking guardrail agent.
    """

    is_on_topic: bool = Field(
        description="True if the user's question is about Python, JavaScript, or SQL. Otherwise, False."
    )
    clarification_message: str = Field(
        description="If the question is off-topic, this is a friendly message to send back to the user."
    )
