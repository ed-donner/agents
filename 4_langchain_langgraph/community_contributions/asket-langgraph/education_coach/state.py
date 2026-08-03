from typing import Annotated, Any, List, Optional

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the tutor's last reply")
    grounding_ok: bool = Field(
        description="False if the tutor asserted course-specific or verifiable facts without support from "
        "course search excerpts or other tools when support was required, or omitted [SOURCE: ...] tags after "
        "using course search. True for purely conceptual coaching with no risky specifics."
    )
    success_criteria_met: bool = Field(
        description="Whether the success criteria have been met"
    )
    user_input_needed: bool = Field(
        description="True if clarification from the student is needed, or the tutor is stuck"
    )


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    evaluator_iterations: int
