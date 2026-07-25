from dotenv import load_dotenv
from agents import Agent
from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime

load_dotenv(override=True)

class EditorialDecision(BaseModel):
    title: str = Field(description="The title of the finding")
    priority: Literal["High", "Medium", "Low"] = Field(description="The priority of the finding")
    editorial_score: float = Field(description="The editorial score of the finding")
    newsletter_section: str = Field(description="The section of the newsletter the finding should be in")
    reasoning: str = Field(description="The reasoning for the decision")

class EditorialOutput(BaseModel):
    decisions: List[EditorialDecision] = Field(description="The decisions for the newsletter")

with open("system_prompts/editorial_prioritizer_prompt.txt", "r") as f:
    editorial_prioritizer_prompt = f"Today's date is {datetime.now().strftime('%Y-%m-%d')}. "
    editorial_prioritizer_prompt += f.read()

editorial_prioritizer_agent = Agent(
    name="Editorial Prioritizer Agent",
    instructions=editorial_prioritizer_prompt,
    model="gpt-4o-mini",
    output_type=EditorialOutput
)
