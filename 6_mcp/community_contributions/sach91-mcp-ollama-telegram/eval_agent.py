from pydantic import BaseModel, Field
from agents import Agent
from base_model import ollama_model_eval


INSTRUCTIONS = (
    "You are a analyst tasked with evaluating the short report for a research query.\n"
    "You have high quality standards and accept only good quality report. "
    "You will be provided with the original query and the report.\n"
    "You should evaluate the quality of the report and tell your judgement as your final output.\n"
    "The final output should be boolean, that you accept the report or not.\n"
    "If you do not accept the report, web search will be performed to gather more information."
    "Note that if the query pertains to recent information, it is better to reject the report and go for web search.\n"
)

class EvalData(BaseModel):
    accept: bool = Field(description="You accept the quality of the concise report or not.")

    reason: str = Field(description="The reason for the evaluation.")


eval_agent = Agent(
    name="EvalAgent",
    instructions=INSTRUCTIONS,
    model=ollama_model_eval,
    output_type=EvalData,
)
