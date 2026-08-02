"""Data models and state definitions"""

from typing import Annotated, TypedDict, List, Any, Optional
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class State(TypedDict):
    """Graph state that flows through nodes"""
    messages: Annotated[List[Any], add_messages]
    stage: str
    company_name: Optional[str]
    role_title: Optional[str]
    company_info: Optional[str]
    prep_guide: Optional[str]
    refinement_count: int


class PlannerOutput(BaseModel):
    """Structured output from the planner LLM"""
    response: str
    stage: Optional[str]
    company_name: Optional[str]
    role_title: Optional[str]

