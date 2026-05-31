"""
Message types for the Australia Scholarship Research pipeline.
"""

from dataclasses import dataclass
from typing import Optional
from autogen_core import AgentId


@dataclass
class Message:
    """Simple content message used between agents."""
    content: str


@dataclass
class ResearchTaskMessage:
    """Message carrying a research task (e.g. for the Researcher agent)."""
    content: str
    query: Optional[str] = None  # e.g. "Australian universities scholarships 2025"


@dataclass
class EvaluationTaskMessage:
    """Message carrying research findings for the Evaluator to verify."""
    content: str
    findings: Optional[str] = None
