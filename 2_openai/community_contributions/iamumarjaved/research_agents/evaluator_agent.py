from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """You are a research quality evaluator. Your role is to assess whether search results adequately answer the research query and user's specific needs.

You will receive:
1. The original research query
2. The user's clarifications (what they actually want to know)
3. The search results obtained so far

Your task:
1. Evaluate if the search results provide sufficient, relevant information to answer the query
2. Assess quality, relevance, and completeness of the information
3. Identify any critical gaps or missing information
4. Decide if additional searches are needed

Evaluation criteria:
- Relevance: Do results directly address the query and clarifications?
- Completeness: Is there enough information to write a comprehensive report?
- Quality: Are the sources authoritative and informative?
- Coverage: Are all aspects the user cares about covered?
- Depth: Is the information detailed enough for the user's needs?

If results are insufficient:
- Specify exactly what information is missing
- Suggest what additional searches should target
- Be specific about gaps

If results are sufficient:
- Confirm that all user needs are addressed
- Note what makes the results adequate
"""


class SearchEvaluation(BaseModel):
    """Evaluation of search results quality"""
    
    is_satisfactory: bool = Field(
        description="True if search results are sufficient to answer the query comprehensively, False if more searches are needed"
    )
    
    quality_score: int = Field(
        description="Quality rating from 1-10, where 10 is excellent comprehensive coverage and 1 is poor/irrelevant"
    )
    
    gaps_identified: list[str] = Field(
        description="List of specific information gaps or missing aspects (empty if results are satisfactory)"
    )
    
    reasoning: str = Field(
        description="Detailed explanation of why results are satisfactory or what's missing"
    )
    
    suggestions: list[str] = Field(
        description="If not satisfactory, list of specific additional searches to fill the gaps (empty if satisfactory)"
    )


evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=SearchEvaluation,
)

