"""
State definitions for the Marketing Website Team sidekick.
"""

from typing import Annotated, TypedDict, List, Any, Optional
from langgraph.graph.message import add_messages


class WebsiteState(TypedDict):
    """
    Shared graph state for the marketing website project.

    - messages: running chat & tool-call history
    - success_criteria: textual description of "done"
    - feedback_on_work: manager/evaluator feedback so far
    - success_criteria_met: whether the product meets the goal
    - user_input_needed: if we need the human to unblock/clarify
    - current_phase: high-level phase of work (home, contact, subscription, qa, done)
    - last_worker: last worker node that ran (for routing back from ToolNode)
    """

    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    current_phase: str  # "plan" | "home" | "contact" | "subscription" | "qa" | "done"
    last_worker: Optional[str]  # "backend" | "frontend" | "qa" | "manager"

