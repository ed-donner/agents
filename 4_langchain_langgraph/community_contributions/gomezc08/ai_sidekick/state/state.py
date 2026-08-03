"""
State of current messages.
"""

from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from typing import Annotated
from typing import List, Any, Optional

class State(BaseModel):
    messages: Annotated[List[Any], add_messages] = Field(description = "Current answer to the query")
    success_criteria: str = Field(description = "What a successful answer looks like")
    success_criteria_met: bool = Field(description = "Whether the criteria defined is met or not")
    feedback_on_work: Optional[str] = Field(description = "Feedback on answer to query (if needed)")
    user_input_needed: bool = Field(description = "Whether the agent needs further user feedback to answer the query")