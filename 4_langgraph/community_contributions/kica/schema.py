"""Schema definitions for the planning sidekick with delegated agents."""

from typing import Annotated, Any, Literal, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class Subtask(BaseModel):
    """A single executable task assigned to a specific agent."""

    task: str = Field(
        description="A clear, executable task. Must be self-contained and not refer to 'previous results'."
    )
    assigned_to: Literal["researcher", "executor"] = Field(
        description="Which agent handles this task: researcher for info gathering, executor for actions."
    )


class PlannerOutput(BaseModel):
    """Output from the planner agent."""

    plan: str = Field(
        description="High-level description of the approach."
    )
    subtasks: list[Subtask] = Field(
        description="Ordered list of tasks, each assigned to researcher or executor."
    )
    success_criteria: str = Field(
        description="How to judge when the work is complete."
    )


class EvaluatorOutput(BaseModel):
    """Output from the evaluator agent."""

    feedback: str = Field(description="Feedback on the work done.")
    success_criteria_met: bool = Field(description="Whether success criteria are satisfied.")
    user_input_needed: bool = Field(
        description="True if user clarification or input is needed."
    )
    replan_needed: bool = Field(
        default=False,
        description="True if the planner should try again with a different approach.",
    )


class State(BaseModel):
    """Graph state for the planning sidekick."""

    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    success_criteria: Optional[str] = None
    feedback_on_work: Optional[str] = None
    success_criteria_met: bool = False
    user_input_needed: bool = False
    plan: Optional[str] = None
    subtasks: Optional[list[Subtask]] = None
    next_subtask_index: int = 0
    subtask_results: list[str] = Field(default_factory=list)
    replan_needed: bool = False
    final_answer: Optional[str] = None
