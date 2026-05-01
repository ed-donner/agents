from __future__ import annotations

import uuid
from typing import Annotated, Optional

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.managed import RemainingSteps
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class WhyNode(TypedDict):
    """One record per hypothesis evaluated in the investigation tree."""
    id: str
    branch_path: str
    depth: int
    hypothesis: str
    gemba_result: str
    gemba_notes: str
    is_root_cause: bool
    countermeasure: str


def make_why_node(branch_path: str, depth: int, hypothesis: str) -> WhyNode:
    return WhyNode(
        id=str(uuid.uuid4()),
        branch_path=branch_path,
        depth=depth,
        hypothesis=hypothesis,
        gemba_result="pending",
        gemba_notes="",
        is_root_cause=False,
        countermeasure="",
    )


def _merge_why_nodes(existing: list[WhyNode], updates: list[WhyNode]) -> list[WhyNode]:
    """Merge-by-branch_path reducer: updates overwrite matching existing nodes."""
    by_path = {n["branch_path"]: n for n in existing}
    for u in updates:
        by_path[u["branch_path"]] = {**by_path.get(u["branch_path"], {}), **u}
    return list(by_path.values())


class OverallState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    phenomenon: str
    domain: str
    equipment_context: str
    domain_context: str
    max_depth: int
    investigation_id: str
    why_nodes: Annotated[list[WhyNode], _merge_why_nodes]
    pending_hypotheses: list[dict]
    active_hypothesis: Optional[dict]
    current_depth: int
    current_branch_path: str
    remaining_steps: RemainingSteps
    report_path: str


class InputState(TypedDict):
    """External-facing input provided to start an investigation."""
    phenomenon: str
    domain: str
    equipment_context: str
    domain_context: str
    max_depth: int
    investigation_id: str


class HypothesisCause(BaseModel):
    """One cause together with its own unique Gemba verification instructions."""
    cause: Annotated[str, Field(min_length=1)] = Field(
        description="A specific, physically verifiable cause for the current problem."
    )
    gemba_instructions: str = Field(
        description="Plain-language instructions an operator should follow to verify "
                    "or refute THIS cause specifically. Must differ from instructions "
                    "given for other causes in the same batch."
    )


class WhyHypothesisOutput(BaseModel):
    """Structured output of the why_generator LLM node."""
    hypotheses: list[HypothesisCause] = Field(
        min_length=1,
        max_length=5,
        description="List of 1–5 hypotheses. Each entry pairs one specific cause with "
                    "DISTINCT Gemba instructions that apply only to that cause."
    )
    domain_context: str = Field(
        description="Relevant technical background or known failure patterns discovered "
                    "via research that informed these hypotheses."
    )


class RootCauseDecision(BaseModel):
    """Structured output of the root_cause_validator LLM node."""
    is_root_cause: bool = Field(
        description="True if fixing this cause would prevent the original phenomenon "
                    "from recurring. False if it is an intermediate symptom."
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in this decision from 0.0 (uncertain) to 1.0 (certain)."
    )
    reasoning: str = Field(
        description="Explanation of why this is or is not the root cause."
    )
    probe_direction: str = Field(
        description="If not a root cause, the underlying mechanism to probe next. "
                    "Empty string if is_root_cause is True."
    )


class CountermeasureOutput(BaseModel):
    """Structured output of the countermeasure_generator LLM node."""
    action: str = Field(description="Specific corrective action to eliminate the root cause.")
    prevention_type: str = Field(
        description="One of: 'immediate', 'systemic', or 'poka-yoke'."
    )
    suggested_owner: str = Field(
        description="Role responsible for implementing this countermeasure."
    )
    deadline_days: int = Field(
        ge=1,
        description="Recommended number of days to implement this countermeasure."
    )
