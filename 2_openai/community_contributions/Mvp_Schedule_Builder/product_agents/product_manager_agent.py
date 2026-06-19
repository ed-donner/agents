from agents import Agent, Tool

from .base_model import InstructionsModel, AgentModel
from .scheduler_agent import SchedulerAgent, Schedule
from tools import sync_schedule_to_calendar


class ProductManagerInstructions(InstructionsModel):
    """Instructions for the Product Manager Agent."""

    @property
    def name(self) -> str:
        return "product_manager_agent"

    @property
    def instructions(self) -> str:
        return """
        You are a product manager agent responsible for overseeing the development of a project schedule based on an initial idea from the user.

        1. Create functional requirements for the project idea based on the market research and the critique of the idea.
        2. Prioritize the requirements based on business value and feasibility.
        3. Collaborate with the scheduler agent to create the schedule for the whole project.
        4. Use the sync_schedule_to_calendar tool to create a Google Calendar with all the scheduled activities.
        5. For the output, only return the schedule result and do not return any other information.
        
        AVAILABLE TOOLS:
        - scheduler_agent: Creates project schedules with activities and timelines
        - sync_schedule_to_calendar: Syncs the created schedule to Google Calendar
        
        WORKFLOW:
        1. Use scheduler agent to create a detailed project schedule
        2. Review the schedule for completeness and feasibility  
        3. Sync the schedule to Google Calendar for easy tracking and collaboration
        """

    @property
    def handoff_description(self) -> str:
        return f"Transfer to product manager agent for overseeing product development and scheduling. \n\n{self.instructions}"

    @property
    def model(self) -> str:
        return "gpt-4o-mini"


class ProductManagerAgent(AgentModel):
    """Agent for managing product development and scheduling."""

    def __init__(self):
        self.agent = self.init_agent()

    def init_agent(self):
        instructions = ProductManagerInstructions()
        scheduler_tool = SchedulerAgent().as_tool()

        agent = Agent(
            name=instructions.name,
            instructions=instructions.instructions,
            model=instructions.model,
            tools=[scheduler_tool, sync_schedule_to_calendar],
            handoff_description=instructions.handoff_description,
            output_type=Schedule
        )

        return agent

    def as_tool(self) -> Tool:
        """Returns the Product Manager Agent as a tool."""
        instructions = ProductManagerInstructions()
        return self.agent.as_tool(
            tool_name=instructions.name,
            tool_description=instructions.handoff_description,
        )
