from __future__ import annotations
from typing import Any, Dict, List, Optional
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict


READY_TOKEN = "<<READY_FOR_VALIDATION>>"
MAX_ITERATIONS = 15
MAX_STEPS = 200


class BuildState(TypedDict, total=False):
    """Shared graph state for the Sidekick workflow."""

    messages: Annotated[List[Any], add_messages]
    user_prompt: str
    rag_context: str
    task_plan: Optional[str]
    workspace_dir: str
    validation_report: Optional[str]
    validation_passed: Optional[bool]
    reviewer_feedback: Optional[str]
    reviewer_passed: Optional[bool]
    diagnosis: Optional[str]
    formatting_errors: Optional[List[str]]
    formatting_warnings: Optional[List[str]]
    iteration: int
    step_count: int
    error_history: Optional[Dict[str, Any]]  # Track repeated errors for circuit breaker
    circuit_breaker_active: Optional[bool]  # Flag when circuit breaker is triggered
    error_type: Optional[str]  # Type of error detected: "test_py_error", "main_py_logic_error", etc.
    logic_fix_attempts: Optional[int]  # Track consecutive logic fix attempts to prevent infinite loops
    count_fix_attempts: Optional[int]  # Track consecutive test count fix attempts
    total_validation_failures: Optional[int]  # Track total validation failures for universal circuit breaker


class ReviewDecision(BaseModel):
    """Structured output produced by the reviewer LLM."""

    verdict: str = Field(description="Short string like PASS or REVISE")
    approved: bool = Field(description="True when the artifacts satisfy the prompt and guidelines")
    feedback: str = Field(description="Detailed feedback, including any change requests")
    notes: Optional[str] = Field(default=None, description="Additional observations or caveats")


ConfigDict = Dict[str, Any]

