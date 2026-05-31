"""
Pydantic models for the trust-aware deep research workflow.

These models enforce structure and accountability throughout the research pipeline.
"""

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class SourceTier(str, Enum):
    """
    Source quality tiers - treats the internet as adversarial.
    
    Priority ladder:
    1. PRIMARY - docs, papers, filings (most trusted)
    2. SECONDARY - reputable news/analysis
    3. VENDOR - allowed but labeled as vendor material
    4. OPINION - blogs/opinion pieces (framing only)
    5. EXCLUDED - social media (not used)
    """
    PRIMARY = "primary"
    SECONDARY = "secondary"
    VENDOR = "vendor"
    OPINION = "opinion"
    EXCLUDED = "excluded"


class Claim(BaseModel):
    """
    A single factual assertion with evidence chain.
    
    Every claim in the ledger must be traceable to a source.
    The writer agent cannot invent facts outside the ledger.
    """
    claim: str = Field(description="A single factual assertion")
    evidence: str = Field(description="Supporting quote or data from the source")
    source_url: str = Field(description="URL where the evidence was found")
    source_domain: str = Field(default="", description="Domain name of the source (e.g., 'cdc.gov')")
    source_publisher_type: str = Field(
        default="unknown", 
        description="Publisher type: government, academic, news, vendor, blog, social, unknown"
    )
    source_tier: SourceTier = Field(description="Quality tier of the source")
    confidence: Literal["low", "medium", "high"] = Field(
        description="Confidence level based on source quality and corroboration"
    )
    notes: str | None = Field(
        default=None,
        description="Caveats, age of information, potential bias, conflicts with other claims"
    )


class ClaimLedger(BaseModel):
    """
    The complete set of validated claims from research.
    
    This is the single source of truth for the report writer.
    No facts may be added to the report that aren't in this ledger.
    """
    claims: list[Claim] = Field(
        default_factory=list,
        description="All validated claims extracted from research"
    )
    conflicts: list[str] = Field(
        default_factory=list,
        description="Notes about conflicting information found across sources"
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Important questions that couldn't be answered from available sources"
    )


class FollowUpQuestions(BaseModel):
    """Questions to ask the user before starting research."""
    questions: list[str] = Field(
        description="Exactly 3 clarifying questions to scope the research"
    )


class ResearchBrief(BaseModel):
    """Locked research specification."""
    topic: str
    intended_use: str
    scope_constraints: str
    desired_angle: Literal["best_case", "risks", "balanced"]
    follow_up_answers: dict[str, str] = Field(default_factory=dict)


class SearchQuery(BaseModel):
    """A single search query with context."""
    query: str = Field(description="The search term to execute")
    reason: str = Field(description="Why this search is important")


class SearchPlan(BaseModel):
    """The complete search strategy."""
    searches: list[SearchQuery] = Field(description="List of searches to perform")
    stop_condition: str = Field(
        default="At least 3 primary sources and 5 total sources",
        description="When to stop searching"
    )
    source_policy_notes: str = Field(
        default="Prioritize primary sources. Exclude social media.",
        description="Guidance for source selection"
    )


class PublisherType(str, Enum):
    """Type of publisher behind a source."""
    GOVERNMENT = "government"
    ACADEMIC = "academic"
    NEWS = "news"
    VENDOR = "vendor"
    BLOG = "blog"
    SOCIAL = "social"
    UNKNOWN = "unknown"


class SearchResult(BaseModel):
    """Raw result from a single search."""
    query: str = Field(description="The query that produced this result")
    url: str = Field(description="URL of the source")
    title: str = Field(description="Page title")
    snippet: str = Field(description="Relevant excerpt from the page")
    domain: str = Field(default="", description="Domain name extracted from URL")
    publisher_type: PublisherType = Field(
        default=PublisherType.UNKNOWN, 
        description="Type of publisher (government, academic, news, vendor, blog, social)"
    )
    inferred_tier: SourceTier = Field(description="Inferred quality tier of this source")


class ReportData(BaseModel):
    """The final report output."""
    short_summary: str = Field(description="A 2-3 sentence summary of findings")
    markdown_report: str = Field(description="The full report in markdown format")
    claims_used: list[str] = Field(
        default_factory=list,
        description="IDs/summaries of claims from the ledger that were used"
    )
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Suggested topics for further research"
    )
