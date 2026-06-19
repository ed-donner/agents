from .base_model import InstructionsModel, AgentModel

from typing import List
from typing import Annotated
from pydantic import Field, BaseModel

from agents import Agent, Tool

from .market_researcher_agent import MarketResearchReport
from .product_manager_agent import ProductManagerAgent


class IdeaCritiquerInstructions(InstructionsModel):
    """Instructions for the Idea Critiquer Agent."""

    @property
    def name(self) -> str:
        return "idea_critiquer"

    @property
    def instructions(self) -> str:
        return """
        You are an idea critiquer agent. Your task is to critically evaluate product ideas based on various criteria such as feasibility, market potential, and innovation.
        1. Given the Market Research Report containing the competitor analysis, customer segment information, target market information and an overall idea rating, provide a detailed critique of the idea. 
        2. For the idea, provide 3 pros and 3 cons about the idea.
        3. Provide ways to simplify, improve or pivot the idea to increase its chances of success.
        """

    @property
    def handoff_description(self) -> str:
        return self.instructions

    @property
    def model(self) -> str:
        return "gpt-4o-mini"


class IdeaCritiqueReport(BaseModel):
    """Represents the critique report for a product idea."""

    pros: Annotated[List[str], Field(min_length=1, max_length=3)]
    cons: Annotated[List[str], Field(min_length=1, max_length=3)]
    suggestions: List[str]

    def __str__(self) -> str:
        pros_str = "\n".join(f"- {pro}" for pro in self.pros)
        cons_str = "\n".join(f"- {con}" for con in self.cons)
        suggestions_str = "\n".join(
            f"- {suggestion}" for suggestion in self.suggestions
        )

        return (
            f"Idea Critique Report:\n\n"
            f"Pros:\n{pros_str}\n\n"
            f"Cons:\n{cons_str}\n\n"
            f"Suggestions for Improvement:\n{suggestions_str}"
        )


class IdeaCritiquerAgent(AgentModel):
    """Agent that critiques product ideas based on market research."""

    market_research_report: MarketResearchReport

    def __init__(self, market_research_report: MarketResearchReport):
        self.market_research_report = market_research_report
        self.agent = self.init_agent()

    def init_agent(self) -> Agent:
        instructions = IdeaCritiquerInstructions()

        agent = Agent(
            output_type=IdeaCritiqueReport,
            name=instructions.name,
            instructions=instructions.instructions
            + f"\n\nMarket Research Report:\n{self.market_research_report}",
            model=instructions.model,
            handoff_description=instructions.handoff_description,
        )

        return agent

    def as_tool(self) -> Tool:
        instructions = IdeaCritiquerInstructions()

        tool = self.agent_instance.as_tool(
            tool_name=instructions.name,
            tool_description=instructions.handoff_description,
        )

        return tool
