from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


DraftStatus = Literal["draft", "approved", "rejected", "published"]
ApprovalStatus = Literal["approved", "rejected", "feedback"]


class SourceItem(BaseModel):
    title: str
    url: str
    snippet: str = ""
    extracted_text: str = ""
    source_type: str = "web"
    score: float = 0.0


class IdeaRecord(BaseModel):
    id: str
    topic: str
    goal: str
    notes: str = ""
    urls: list[str] = Field(default_factory=list)
    created_at: str


class ResearchBundleRecord(BaseModel):
    id: str
    idea_id: str
    query: str
    summary: str
    sources: list[SourceItem] = Field(default_factory=list)
    created_at: str


class DraftInput(BaseModel):
    variant: str
    title: str
    body: str
    cta: str = ""
    link_url: str | None = None
    confidence: str = "medium"
    score: float = 0.0
    rationale: str = ""


class DraftRecord(BaseModel):
    id: str
    idea_id: str
    bundle_id: str
    parent_draft_id: str | None = None
    variant: str
    title: str
    body: str
    cta: str = ""
    link_url: str | None = None
    confidence: str = "medium"
    score: float = 0.0
    rationale: str = ""
    similarity_score: float = 0.0
    status: DraftStatus = "draft"
    created_at: str
    updated_at: str


class ApprovalDecisionRecord(BaseModel):
    id: str
    draft_id: str
    decision: ApprovalStatus
    feedback: str = ""
    created_at: str


class PublishedPostRecord(BaseModel):
    id: str
    draft_id: str
    post_urn: str
    author_urn: str
    payload: dict[str, Any]
    response: dict[str, Any]
    link_url: str | None = None
    created_at: str


class VoiceExampleRecord(BaseModel):
    id: str
    content: str
    source_label: str
    created_at: str


class OAuthSessionMetadata(BaseModel):
    id: str = "default"
    member_sub: str
    person_urn: str
    name: str
    email: str | None = None
    access_token_ref: str
    expires_at: str
    created_at: str
    updated_at: str
