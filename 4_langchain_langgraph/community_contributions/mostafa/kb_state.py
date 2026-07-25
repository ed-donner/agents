import operator
from typing import Annotated, TypedDict
from models import (
    ApprovedSource,
    ResearchPlan,
    RejectedSource,
    RetrievedSource,
    KBEntry,
)


class KBState(TypedDict):
    # Input
    topic: str
    kb_name: str

    # Planning phase
    research_plan: ResearchPlan | None
    plan_feedback: list[str]
    plan_revision_count: int

    # Search phase
    raw_sources: list[RetrievedSource]

    # SME source review
    approved_sources: list[ApprovedSource]
    rejected_sources: list[RejectedSource]

    # Processing phase
    kb_entries: list[KBEntry]

    # Shared
    messages: Annotated[list[dict], operator.add]  # agent communication log
