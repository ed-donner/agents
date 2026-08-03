"""
Australia Scholarship Research — AutoGen pipeline with Creator, Researcher, and Evaluator.
State-driven flow (LangGraph-style); all agents use Serper and Playwright tools.
"""

from .states import ScholarshipResearchState, Phase
from .messages import Message, ResearchTaskMessage, EvaluationTaskMessage
from .orchestrator import run_pipeline

__all__ = [
    "ScholarshipResearchState",
    "Phase",
    "Message",
    "ResearchTaskMessage",
    "EvaluationTaskMessage",
    "run_pipeline",
]
