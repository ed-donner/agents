from typing import Annotated, List, Any, Optional, TypedDict
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback: Optional[str]
    last_assistant: str
    success_criteria_met: bool
    user_input_needed: bool
    executor_output: Optional[str]
