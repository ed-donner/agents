from .base_model import InstructionsModel, AgentModel
from pydantic import BaseModel

from typing import List

from agents import Agent, Tool, WebSearchTool

MAX_SEARCH_RESULTS = 3

INSTRUCTIONS = f"""
    You are a market researcher agent. Your task is to conduct thorough market research for new product ideas.
    1. For each product idea, analyze the target market.
    2. Identify upto f{MAX_SEARCH_RESULTS} key competitors, and identify the strengths and weaknesses of their product offering.
    3. Identify and describe the main customer segments for the product idea.
    4. Provide a rating for the idea based on market viability, novely and potential for success.
"""


class MarketResearcherInstructions(InstructionsModel):
    @property
    def name(self) -> str:
        return "market_researcher"

    @property
    def instructions(self) -> str:
        return INSTRUCTIONS

    @property
    def handoff_description(self) -> str:
        return self.instructions()

    @property
    def model(self) -> str:
        return "gpt-4o-mini"


class Competitor(BaseModel):
    """Represents a competitor in the market research."""

    name: str
    product_description: str
    strengths: str
    weaknesses: str


class CustomerSegment(BaseModel):
    """Represents a customer segment in the market research."""

    segment_name: str
    demographics: str
    needs: str
    preferences: str


class IdeaRating(BaseModel):
    """Rating for a product idea based on market research."""

    feasibility: int  # Rating from 1 to 10
    market_potential: int  # Rating from 1 to 10
    innovation: int  # Rating from 1 to 10
    overall_score: float  # Average of the above ratings


class MarketResearchReport(BaseModel):
    """Represents the market research report for a product idea."""

    idea: str
    target_market: List[str]
    competitors: List[Competitor]
    customer_segments: List[CustomerSegment]

    def __str__(self) -> str:
        """Formats the market research report as a string."""

        report = f"Market Research Report for Idea: {self.idea}\n\n"
        report += "Target Market:\n"
        for market in self.target_market:
            report += f"- {market}\n"

        report += "\nCompetitors:\n"
        for competitor in self.competitors:
            report += (
                f"Name: {competitor.name}\n"
                f"Product Description: {competitor.product_description}\n"
                f"Strengths: {competitor.strengths}\n"
                f"Weaknesses: {competitor.weaknesses}\n\n"
            )

        report += "Customer Segments:\n"
        for segment in self.customer_segments:
            report += (
                f"Segment Name: {segment.segment_name}\n"
                f"Demographics: {segment.demographics}\n"
                f"Needs: {segment.needs}\n"
                f"Preferences: {segment.preferences}\n\n"
            )

        return report


class MarketResearcherAgent(AgentModel):
    """Agent that conducts market research for product ideas."""

    def __init__(self):
        self.agent = self.init_agent()

    def init_agent(self):
        instructions = MarketResearcherInstructions()
        agent = Agent(
            name=instructions.name,
            instructions=instructions.instructions,
            model=instructions.model,
            output_type=MarketResearchReport,
            tools=[WebSearchTool(search_context_size="low")],
        )

        return agent

    def as_tool(self) -> Tool:
        instructions = MarketResearcherInstructions()
        tool = self.agent_instance.as_tool(
            tool_name=instructions.name,
            tool_description=instructions.handoff_description,
        )
        return tool
