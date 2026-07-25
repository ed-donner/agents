from pydantic import BaseModel, Field
from agents import Agent

class ResearchEvaluation(BaseModel):
    is_acceptable: bool = Field(description="Whether the research report is acceptable or not")
    feedback: str = Field(description="Feedback on the research report that guided the decision to accept the report or not.")

research_evaluator_instructions = f"You are a research report evaluator that decides whether a research report is adequate for a user's given input. esponse to a question is acceptable. \
You are provided with a report created by an Agent and a query given by a user. Your task is to decide whether the Agent's latest report is of acceptable quality. \
The Agent has been instructed to produce a concise 2-3 paragraph summary (less than 300 words) of the results, capturing the essence and ignoring any fluff and without including any additional commentary than the summary itself. \
"


research_evaluator_agent = Agent(
    name="ResearchEvaluationAgent",
    instructions=research_evaluator_instructions,
    model="gpt-4o-mini",
    output_type=ResearchEvaluation,
)