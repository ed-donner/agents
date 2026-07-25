"""
State definitions for the Australia Scholarship Research flow (LangGraph-style).

State is passed through: research_request -> researcher_findings -> evaluator_verdict.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any
from enum import Enum


class Phase(str, Enum):
    """Current phase of the research pipeline."""
    INIT = "init"
    RESEARCH_REQUESTED = "research_requested"
    RESEARCHER_RUNNING = "researcher_running"
    RESEARCHER_DONE = "researcher_done"
    EVALUATOR_RUNNING = "evaluator_running"
    EVALUATOR_DONE = "evaluator_done"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class ScholarshipResearchState:
    """
    Shared state for the Australia scholarship research pipeline.

    - research_request: the user/orchestrator request (e.g. "Australian universities scholarships")
    - researcher_findings: raw output from the researcher agent
    - evaluator_verdict: evaluator's assessment (correctness, scholarship-related)
    - current_phase: current step in the pipeline
    - error: optional error message if something failed
    - metadata: extra data (e.g. which agents were created)
    """
    research_request: str = ""
    researcher_findings: Optional[str] = None
    evaluator_verdict: Optional[str] = None
    current_phase: Phase = Phase.INIT
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "research_request": self.research_request,
            "researcher_findings": self.researcher_findings,
            "evaluator_verdict": self.evaluator_verdict,
            "current_phase": self.current_phase.value,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ScholarshipResearchState":
        phase = Phase(d.get("current_phase", "init"))
        return cls(
            research_request=d.get("research_request", ""),
            researcher_findings=d.get("researcher_findings"),
            evaluator_verdict=d.get("evaluator_verdict"),
            current_phase=phase,
            error=d.get("error"),
            metadata=d.get("metadata", {}),
        )
