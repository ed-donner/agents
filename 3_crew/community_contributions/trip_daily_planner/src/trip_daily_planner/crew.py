from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from typing import List, Optional
from pydantic import BaseModel, Field
from tools.email_tool import SendEmailTool


class Activity(BaseModel):
    name: str = Field(..., description="Name of the activity")
    location: str = Field(..., description="Location of the activity")
    description: str = Field(..., description="Description of the activity")
    reviews: Optional[List[str]] = Field(..., description="List of reviews")
    rating: Optional[float] = Field(..., description="Rating of the activity")

class Restaurant(BaseModel):
    name: str = Field(..., description="Name of the restaurant")
    location: str = Field(..., description="Address of the restaurant")
    cuisine_type: str = Field(..., description="Type of cuisine")
    reviews: Optional[List[str]] = Field(..., description="List of reviews")   

class DayPlan(BaseModel):
	day: str = Field(..., description="Each day of the trip like 'Day 1', 'Day 2' etc.")
	activities: List[Activity] = Field(..., description="List of activities")
	restaurants: List[Restaurant] = Field(..., description="List of restaurants")

class Itinerary(BaseModel):
    name: str = Field(..., description="Name of Itinerary, something funny")
    day_plans: List[DayPlan] = Field(..., description="List of day plans")


@CrewBase
class TripDailyPlanner():
    """TripDailyPlanner crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def personalized_activity_planner(self) -> Agent:
        # Keep n_results=3; otherwise, it will trigger rate limit error: exceeds 30,000 tokens per minutes
        return Agent(
            config=self.agents_config['personalized_activity_planner'],
            tools=[SerperDevTool(n_results=3), ScrapeWebsiteTool()],
            max_retry_limit=1,
            max_iter=2,
            respect_context_window=True, 
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def restaurant_scout(self) -> Agent:
        return Agent(
            config=self.agents_config['restaurant_scout'],
            tools=[SerperDevTool(n_results=3), ScrapeWebsiteTool()],
            max_retry_limit=1,
            max_iter=2,
            respect_context_window=True, 
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def itinerary_compiler(self) -> Agent:
        return Agent(
            config=self.agents_config['itinerary_compiler'],
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def email_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['email_agent'],
            tools=[SendEmailTool()],
            allow_delegation=False,
        )                 

    @task
    def personalized_activity_planning_task(self) -> Task:
        return Task(
            config=self.tasks_config['personalized_activity_planning_task'],
        )

    @task
    def restaurant_location_scout_task(self) -> Task:
        return Task(
            config=self.tasks_config['restaurant_location_scout_task'],
        )

    @task
    def itinerary_compilation_task(self) -> Task:
        return Task(
            config=self.tasks_config['itinerary_compilation_task'],
            output_pydantic=Itinerary,
        )    

    @task
    def format_send_email_task(self) -> Task:
        return Task(
            config=self.tasks_config['format_send_email_task'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the TripDailyPlanner crew"""
       
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
