from typing import List

from pydantic import BaseModel, Field


class LeadContext(BaseModel):
    company: str
    industry: str
    pain_point: str
    value_prop: str


class EmailDraft(BaseModel):
    subject: str = Field(description="Subject line for the email")
    body: str = Field(description="Plain-text email body")
    cta: str = Field(description="Clear call-to-action")


class DraftScore(BaseModel):
    score: int = Field(ge=1, le=10)
    critique: str


class FollowUpSequence(BaseModel):
    follow_ups: List[str] = Field(description="2-3 follow-up emails, each under 80 words")


class HtmlEmail(BaseModel):
    subject: str
    html_body: str = Field(description="Clean HTML email body")
    text_body: str = Field(description="Plain-text email body")


class SendPayload(BaseModel):
    to_email: str
    subject: str
    text_body: str
    html_body: str | None = None


class ClarifyingQuestions(BaseModel):
    questions: List[str] = Field(description="Short clarifying questions to ask before researching")


class GuardrailDecision(BaseModel):
    allowed: bool
    reason: str
