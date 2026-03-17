"""LangGraph state schema shared across all agent nodes."""

from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """Mutable state passed between agent nodes."""

    # Full conversation history
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)

    # The user's intent resolved by the router
    intent: str = ""

    # Raw data fetched by tool nodes (cleared each turn)
    tool_data: dict = Field(default_factory=dict)

    # Final text response assembled by the responder
    response: str = ""

    class Config:
        arbitrary_types_allowed = True
