from pydantic import BaseModel
from agents import Agent, Tool
from typing import List

from .base_model import InstructionsModel, AgentModel
from datetime import date


class SchedulerInstructions(InstructionsModel):
    """Instructions for the Scheduler Agent."""

    def __init__(self, num_weeks: int = 4):
        self.num_weeks = num_weeks

    @property
    def name(self) -> str:
        return "scheduler_agent"

    @property
    def instructions(self) -> str:
        return f"""
        You are a project scheduler agent. Your task is to create and manage project schedules based on given tasks, deadlines, and resource availability.
        Assume that the project is done by a team of 1. 
        The project timeline is {self.num_weeks} weeks starting on the date: {date.today()}.
        
        1. Given the list of functional requirements, break them down into manageable tasks.
        2. Estimate the time required for each task and assign deadlines.
        3. Spread tasks across the {self.num_weeks}-week project timeline, ensuring that dependencies are respected. The tasks can be assigned to single or multiple days. 
        """

    @property
    def handoff_description(self) -> str:
        return f"Transfer to scheduler agent for creating {self.num_weeks}-week project schedules. \n\n{self.instructions}"

    @property
    def model(self) -> str:
        return "gpt-4o-mini"


class Activity(BaseModel):
    """Represents a single activity or task in the schedule."""

    name: str
    start_date: str
    end_date: str
    description: str


class Schedule(BaseModel):
    """Represents the project schedule."""

    calendar_name: str
    activities: List[Activity]
    project_start_date: str = None

    def __str__(self) -> str:
        """Formats the schedule into a readable string with improved formatting."""

        if not self.activities:
            return f"Schedule: {self.calendar_name}\nNo activities scheduled."

        # Create header
        output = [f"📅 Schedule: {self.calendar_name}"]
        output.append("=" * 50)

        # Sort activities by start date for chronological order
        sorted_activities = sorted(self.activities, key=lambda x: x.start_date)

        # Format each activity with improved layout
        for i, activity in enumerate(sorted_activities, 1):
            activity_block = [
                f"\n🔹 Activity #{i}: {activity.name}",
                f"   📅 Duration: {activity.start_date} → {activity.end_date}",
                f"   📝 Description: {activity.description}",
                "   " + "-" * 40,
            ]
            output.extend(activity_block)

        # Add summary
        output.append(f"\n📊 Total Activities: {len(self.activities)}")

        return "\n".join(output)


class SchedulerAgent(AgentModel):
    """Agent that creates and manages project schedules based on given tasks and deadlines."""

    def __init__(self):
        self.agent = self.init_agent()

    def init_agent(self) -> Agent:
        instructions = SchedulerInstructions()

        agent = Agent(
            output_type=Schedule,
            name=instructions.name,
            instructions=instructions.instructions,
            model=instructions.model,
        )

        return agent

    def as_tool(self, num_weeks=4) -> Tool:
        instructions = SchedulerInstructions(num_weeks=num_weeks)

        tool = self.agent_instance.as_tool(
            tool_name=instructions.name,
            tool_description=instructions.handoff_description,
        )

        return tool
