from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from datetime import datetime


# ─── Shared Enums ───

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Decision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


# ─── Research Planner Output ───

class Subtopic(BaseModel):
    name: str = Field(description="Short name for this subtopic")
    description: str = Field(description="What this subtopic covers")
    search_queries: list[str] = Field(
        description="2-5 specific search queries for this subtopic"
    )
    priority: Priority = Field(description="Importance of this subtopic")

class ResearchPlan(BaseModel):
    topic: str = Field(description="The target domain being researched")
    rationale: str = Field(description="Why this breakdown makes sense")
    subtopics: list[Subtopic] = Field(description="List of subtopics to research")


# ─── SME Plan Review Output ───

class PlanReview(BaseModel):
    decision: Decision = Field(description="Whether to approve or reject the plan")
    reasoning: str = Field(description="Overall evaluation of the plan")
    feedback: Optional[list[str]] = Field(
        default=None,
        description="Specific actionable points for revision — required if rejected"
    )


# ─── Search & Retrieval Output ───

class RetrievedSource(BaseModel):
    subtopic: str = Field(description="Which subtopic this source relates to")
    query: str = Field(description="Which search query found this source")
    url: str = Field(description="Source URL")
    title: str = Field(description="Page title")
    snippet: str = Field(description="Short snippet from search results")
    content: str = Field(description="Extracted raw text content")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp of retrieval"
    )

class RetrievalResult(BaseModel):
    sources: list[RetrievedSource] = Field(description="All retrieved sources")


# ─── SME Source Review Output ───

class ApprovedSource(BaseModel):
    url: str
    title: str
    content: str
    subtopic: str
    evaluation: str = Field(description="Brief reason for approval")

class RejectedSource(BaseModel):
    url: str
    reason: str = Field(description="Why this source was rejected")

class SourceReview(BaseModel):
    approved_sources: list[ApprovedSource] = Field(
        description="Sources that passed quality evaluation"
    )
    rejected_sources: list[RejectedSource] = Field(
        description="Sources that failed quality evaluation"
    )


# ─── Content Processor Output ───

class KBMetadata(BaseModel):
    chunk_index: int = Field(description="Index of this chunk within the source")
    topic: str = Field(description="Main topic this entry belongs to")
    subtopic: str = Field(description="Subtopic this entry belongs to")
    retrieved_at: str = Field(description="When the source was retrieved")
    author: Optional[str] = Field(default=None, description="Author of the original source")
    publication_date: Optional[str] = Field(default=None, description="Publication date of the original source")

class KBEntry(BaseModel):
    # id: str = Field(description="Unique identifier for this chunk")
    source_url: str = Field(description="Original source URL")
    source_title: str = Field(description="Original source title")
    subtopic: str = Field(description="Related subtopic")
    # chunk_index: int = Field(description="Index of this chunk within the source")
    content: str = Field(description="Cleaned markdown text of this chunk")
    metadata: KBMetadata = Field(description="Metadata for this KB entry")

class KBOutput(BaseModel):
    entries: list[KBEntry] = Field(description="All processed KB entries")

