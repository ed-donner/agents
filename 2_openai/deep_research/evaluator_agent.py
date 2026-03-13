"""Evaluator: scores the report and decides if it needs refinement. Optimizer: improves report from feedback."""
from pydantic import BaseModel, Field
from typing import List
from agents import Agent

EVALUATION_INSTRUCTIONS = """
You are a Research Quality Evaluator. Assess the research report and decide if it needs refinement.

Evaluate on:
1. **Completeness**: Does it thoroughly address the original query and any clarifications?
2. **Accuracy & sources**: Are facts well-sourced? Is there a Sources/References section?
3. **Clarity & structure**: Is it clear, well-structured, and easy to follow?
4. **Depth**: Sufficient analysis and substance (not surface-level)?
5. **Relevance**: All content relevant to the query?
6. **Source diversity (guardrail)**: Check the `## Sources and References` section. Prefer at least 3 distinct sources and avoid over-reliance on a single site or domain.
   - If there are fewer than 3 distinct sources, or if one source/domain clearly accounts for the majority of citations, treat this as a serious weakness.
   - In such cases, lower the overall_score accordingly and set needs_refinement=True, with explicit suggestions to broaden and diversify the sources.

Scoring: 9-10 Excellent, 7-8 Good, 5-6 Adequate, 1-4 Poor. A report without proper source citations or with very weak source diversity should not score above 6.
If needs_refinement is True, provide specific, actionable suggestions (including, when relevant, how to diversify sources).
"""


class EvaluationFeedback(BaseModel):
    overall_score: int = Field(description="Quality score from 1-10", ge=1, le=10)
    strengths: List[str] = Field(description="What the report does well")
    weaknesses: List[str] = Field(description="Areas needing improvement")
    suggestions: List[str] = Field(description="Specific suggestions for improvement")
    needs_refinement: bool = Field(description="True if the report should be improved before finalizing")


evaluator_agent = Agent(
    name="ResearchEvaluator",
    instructions=EVALUATION_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=EvaluationFeedback,
)

OPTIMIZER_INSTRUCTIONS = """
You are a Research Report Optimizer. You receive an original research report and evaluation feedback with improvement suggestions.
Create an improved version that addresses the feedback while keeping factual content accurate.
Improve structure, flow, clarity, completeness, and presentation. Do not invent new facts.
"""


class OptimizedReport(BaseModel):
    improved_markdown_report: str = Field(description="The refined report in markdown")
    optimization_notes: str = Field(description="Brief note on what was improved")


optimizer_agent = Agent(
    name="ResearchOptimizer",
    instructions=OPTIMIZER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=OptimizedReport,
)

evaluator_agent_tool = evaluator_agent.as_tool(
    tool_name="evaluate_report",
    tool_description="Evaluate a research report for quality, completeness, and sources. Returns score, suggestions, and whether refinement is needed.",
)
optimizer_agent_tool = optimizer_agent.as_tool(
    tool_name="optimize_report",
    tool_description="Improve a report using evaluator suggestions. Pass the report text and the list of suggestions.",
)
