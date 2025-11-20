"""
Research Agents package for Deep Research AI

This package contains all the specialized agents:
- clarification_agent: Asks clarifying questions
- planner_agent: Creates search strategies
- search_agent: Performs web searches
- evaluator_agent: Evaluates search quality
- writer_agent: Writes research reports
- email_agent: Sends email reports
"""

from .clarification_agent import clarification_agent, ClarifyingQuestions
from .planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from .search_agent import search_agent
from .evaluator_agent import evaluator_agent, SearchEvaluation
from .writer_agent import writer_agent, ReportData
from .email_agent import email_agent

__all__ = [
    'clarification_agent',
    'ClarifyingQuestions',
    'planner_agent',
    'WebSearchItem',
    'WebSearchPlan',
    'search_agent',
    'evaluator_agent',
    'SearchEvaluation',
    'writer_agent',
    'ReportData',
    'email_agent',
]

