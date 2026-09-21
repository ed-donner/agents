from pydantic import BaseModel
from typing import List
from agents import Agent

class EvaluationResult(BaseModel):
    overall_score: int
    """Overall quality score from 1-10"""
    
    strengths: List[str]
    """List of report strengths"""
    
    weaknesses: List[str]
    """List of areas needing improvement"""
    
    suggestions: List[str]
    """Specific suggestions for improvement"""
    
    needs_refinement: bool
    """Whether the report needs to be refined"""
    
    refined_requirements: str
    """If refinement needed, what specific requirements should guide it"""

EVALUATION_INSTRUCTIONS = """
You are a Research Quality Evaluator. Your job is to assess the quality of research reports and determine if they need refinement.

Evaluate reports based on:
1. **Completeness**: Does it thoroughly address the original query?
2. **Accuracy**: Are the facts presented accurate and well-sourced?
3. **Sources & Citations**: Does it include proper source links and references? Is there a "Sources and References" section?
4. **Clarity**: Is the writing clear and well-structured?
5. **Depth**: Does it provide sufficient depth and analysis?
6. **Relevance**: Is all content relevant to the query?

Scoring scale:
- 9-10: Excellent, no refinement needed
- 7-8: Good, minor improvements could help
- 5-6: Adequate, would benefit from refinement
- 1-4: Poor, definitely needs refinement

CRITICAL: A report without proper source citations should not score above 6, regardless of other qualities.

If needs_refinement is True, provide specific, actionable requirements for improvement.
"""

evaluator_agent = Agent(
    name="Research Evaluator",
    instructions=EVALUATION_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=EvaluationResult,
)


class OptimizedReport(BaseModel):
    improved_markdown_report: str
    """The refined and improved version of the report"""
    
    optimization_notes: str
    """Notes on what was improved and why"""

OPTIMIZER_INSTRUCTIONS = """
You are a Research Report Optimizer. You receive:
1. An original research report
2. Evaluation feedback with specific improvement suggestions
3. The original query for context

Your job is to create an improved version that addresses all the feedback while maintaining the factual content.

Focus on:
- Improving structure and flow
- Adding missing analysis or details
- Clarifying confusing sections
- Ensuring complete coverage of the query
- Enhancing readability and presentation

Keep all factual content accurate - only improve presentation, structure, and completeness.
"""

optimizer_agent = Agent(
    name="Research Optimizer", 
    instructions=OPTIMIZER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=OptimizedReport,
) 