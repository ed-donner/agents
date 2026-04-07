"""Pydantic models shared across planner, clarification, and expansion agents."""

from pydantic import BaseModel, Field, model_validator


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search matters for the research brief.")
    query: str = Field(description="Search query for the web.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="Ordered list of web searches to run for the brief."
    )


class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(
        description="Exactly three focused questions to narrow scope, audience, or depth.",
        min_length=3,
        max_length=3,
    )


class FollowUpPlan(BaseModel):
    need_follow_up: bool = Field(
        description="True only if additional web search would materially improve the report."
    )
    searches: list[WebSearchItem] = Field(
        default_factory=list,
        description="Zero to three extra searches; never more than three.",
    )

    @model_validator(mode="after")
    def cap_at_three(self):
        if len(self.searches) > 3:
            self.searches = self.searches[:3]
        if not self.need_follow_up:
            self.searches = []
        return self
