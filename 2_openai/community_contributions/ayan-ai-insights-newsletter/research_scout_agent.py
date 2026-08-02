from dotenv import load_dotenv
from agents import Agent
from agents import WebSearchTool
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

load_dotenv(override=True)

class ResearchFinding(BaseModel):
    title: str = Field(description="The title of the finding")
    category: str = Field(description="The category of the finding")
    summary: str = Field(description="A summary of the finding")
    why_it_matters: str = Field(description="Why this finding is important")
    source_links: List[str] = Field(description="The source links of the finding")
    published_date: str = Field(description="The published date of the finding")
    signal_score: int = Field(description="The signal score of the finding")

class ResearchScoutOutput(BaseModel):
    findings: List[ResearchFinding] = Field(description="The findings of the research")

web_search_tool = WebSearchTool()

with open("system_prompts/research_agent_prompt.txt", "r") as f:
    research_agent_prompt = f"Today's date is {datetime.now().strftime('%Y-%m-%d')}. "
    research_agent_prompt += f.read()

research_agent = Agent(
    name="Research Agent",
    instructions=research_agent_prompt,
    model="gpt-4o-mini",
    tools=[web_search_tool],
    output_type=ResearchScoutOutput
)
