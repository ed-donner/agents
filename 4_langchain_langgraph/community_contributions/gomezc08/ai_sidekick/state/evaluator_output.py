"""
Current state on Evaluation of output
"""

from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from typing import Annotated

class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )