from typing import Literal
from pydantic import BaseModel, Field, model_validator
import json


RoleAgent = Literal["Agent"]
RoleUser = Literal["User"]


class Question(BaseModel):
    role: RoleAgent = Field(default="Agent", description="Always 'Agent'")
    reasoning: str = Field(description="Why this question matters now.")
    question: str = Field(description="One precise clarifying question.")


class Answer(BaseModel):
    role: RoleUser = Field(default="User", description="Always 'User'")
    answer: str = Field(description="User's answer.")


class QAItem(BaseModel):
    question: Question
    answer: Answer | None = None


class ResearchContext(BaseModel):
    initial_query: str = Field(..., description="Original user query.")
    qa_history: list[QAItem] = Field(default_factory=list)

    def to_json_str(self) -> str:
        """Compact JSON string for feeding into prompts."""
        return json.dumps(self.model_dump(exclude_none=True), separators=(",", ":"))

    def to_system_content(self) -> str:
        return f"RESEARCH_CONTEXT_JSON:\n```json\n{self.to_json_str()}\n```"

    def to_transcript(self) -> list[dict[str, str]]:
        role_map = {"Agent": "assistant", "User": "user"}
        transcript = [{"role": "user", "content": self.initial_query}]

        for qa in self.qa_history:
            transcript.append({
                "role": role_map[qa.question.role],
                "content": qa.question.question
            })
            if qa.answer:
                transcript.append({
                    "role": role_map[qa.answer.role],
                    "content": qa.answer.answer
                })

        return transcript

    def to_input_data(self) -> list[dict[str, str]]:
        return [{
            "role": "system",
            "content": self.to_system_content()
        }] + self.to_transcript()


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")

    def to_json_str(self) -> str:
        """Compact JSON string for feeding into prompts."""
        return json.dumps(self.model_dump(exclude_none=True), separators=(",", ":"))


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_no_duplicates(self):
        qs = [s.query.strip().lower() for s in self.searches]
        if len(qs) != len(set(qs)):
            raise ValueError("Duplicate search queries are not allowed.")
        return self


class SearchResult(BaseModel):
    query: str = Field(description="The search term used for the web search.")
    summary: str = Field(description="Concise summary of the web search results")


class ExecutedSearchPlan(BaseModel):
    results: list[SearchResult]


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


class EmailStatus(BaseModel):
    subject: str = Field(description="Appropriate subject line for an email.")
    status: Literal["success", "failed"]  = Field(description="Delivery status of the email.")
    error_message: str | None = Field(
        default=None,
        description="Optional error message if sending failed."
    )
