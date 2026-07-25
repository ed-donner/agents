"""Structured outputs for workflow automation (Judge)."""

from typing import Literal

from pydantic import BaseModel, Field


class JudgeFeedback(BaseModel):
    """Structured feedback from the Judge agent."""

    status: Literal["pass", "fail"] = Field(
        description="Whether the research is sufficient ('pass') or needs more work ('fail')."
    )
    feedback: str = Field(
        description="Detailed feedback on what is missing. If 'pass', a brief confirmation."
    )
