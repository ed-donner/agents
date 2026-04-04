from __future__ import annotations

import uuid
from operator import add
from typing import Annotated, Optional

from langgraph.managed import RemainingSteps
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Why-tree node — one record per hypothesis evaluated
# ---------------------------------------------------------------------------

class WhyNode(TypedDict):
    id: str
    branch_path: str        # dotted path, e.g. "1", "1.2", "1.2.1"
    depth: int              # 1-based depth level
    hypothesis: str         # the proposed cause
    gemba_result: str       # "OK" | "NOK" | "pending"
    gemba_notes: str        # operator's observations at Gemba
    is_root_cause: bool     # validator's decision
    countermeasure: str     # populated only at confirmed root cause nodes


def make_why_node(
    branch_path: str,
    depth: int,
    hypothesis: str,
) -> WhyNode:
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


# ---------------------------------------------------------------------------
# Graph State
# ---------------------------------------------------------------------------

class OverallState(TypedDict):
    # Investigation context
    phenomenon: str
    domain_context: str
    max_depth: int
    investigation_id: str

    # Growing why-tree (append reducer — never overwritten)
    why_nodes: Annotated[list[WhyNode], add]

    # Queue of hypotheses waiting for Gemba Check (overwrite reducer)
    pending_hypotheses: list[dict]      # list of {hypothesis, branch_path, depth}
    active_hypothesis: Optional[dict]   # the one currently under Gemba Check

    # Tracking
    current_depth: int
    current_branch_path: str

    # Graceful recursion-limit handling
    remaining_steps: RemainingSteps

    # Populated by report_generator
    report_path: str


class InputState(TypedDict):
    """External-facing input — what the caller provides to start an investigation."""
    phenomenon: str
    domain_context: str
    max_depth: int
    investigation_id: str


# ---------------------------------------------------------------------------
# Structured LLM output schemas
# ---------------------------------------------------------------------------

class WhyHypothesisOutput(BaseModel):
    """Output of the why_generator LLM node."""
    causes: list[str] = Field(
        description="List of 1–4 specific possible causes for the current phenomenon. "
                    "Be concrete and testable — each should be something an operator can physically verify."
    )
    gemba_instructions: str = Field(
        description="Plain-language instructions for what the operator should physically "
                    "check or observe to verify or refute these causes."
    )
    domain_context: str = Field(
        description="Relevant technical background or known failure patterns discovered "
                    "via research that informed these hypotheses."
    )


class RootCauseDecision(BaseModel):
    """Output of the root_cause_validator LLM node."""
    is_root_cause: bool = Field(
        description="True if the confirmed cause is a genuine root cause that, if fixed, "
                    "would prevent recurrence. False if it is an intermediate symptom."
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in this decision from 0.0 (uncertain) to 1.0 (certain)."
    )
    reasoning: str = Field(
        description="Explanation of why this is or is not the root cause."
    )
    probe_direction: str = Field(
        description="If not a root cause, what underlying mechanism should be probed next. "
                    "Empty string if is_root_cause is True."
    )


class CountermeasureOutput(BaseModel):
    """Output of the countermeasure_generator LLM node."""
    action: str = Field(
        description="Specific corrective action to eliminate the root cause."
    )
    prevention_type: str = Field(
        description="One of: 'immediate' (quick fix), 'systemic' (process change), "
                    "or 'poka-yoke' (mistake-proofing)."
    )
    suggested_owner: str = Field(
        description="Role or function responsible for implementing this countermeasure "
                    "(e.g. 'Maintenance Technician', 'Process Engineer', 'Quality Manager')."
    )
    deadline_days: int = Field(
        ge=1,
        description="Recommended number of days to implement this countermeasure."
    )
