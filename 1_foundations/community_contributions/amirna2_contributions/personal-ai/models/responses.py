from typing import List
from pydantic import BaseModel


class StructuredResponse(BaseModel):
    """Structured response with reasoning and evidence."""
    response: str
    reasoning: str
    tools_used: List[str]
    facts_used: List[str]
