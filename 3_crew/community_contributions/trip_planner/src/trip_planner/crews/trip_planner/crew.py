from tabnanny import verbose
from pydantic import Field, BaseModel
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional
from datetime import date
from crewai_tools import SerperDevTool
from openai import OpenAI, max_retries

class TripLocation(BaseModel):
    """Location alligned with the trip requirements"""
    location: str = Field(description="Location name")

class TripLocationList(BaseModel):
    """List of locations for trip"""
    Locations: List[TripLocation] = Field(description="List of Trip locations")

class TripItinerary(BaseModel):
    """Itinerary for the trip"""
    location: str = Field(description="location name for the trip")

print(date)
class DailyItinerary(BaseModel):
    day_number: int = Field(description="Day number of the trip (starting from 1)")
    trip_date: date | None = Field(default=None, description="Calendar date for the itinerary day")
    location: str = Field(description="Primary location or city for the day")
    activities: List[str] = Field(description="Planned activities and experiences for the day")
    transportation: Optional[str] = Field(description="Transportation details for the day")
    meals: Optional[str] = Field(description="Meal plans or dining highlights for the day")
    notes: Optional[str] = Field(description="Additional notes or special considerations for the day")

class TripItinerary(BaseModel):
    trip_name: str = Field(description="Name or title of the trip")
    destination: str = Field(description="Overall destination or region of the trip")
    trip_start_date: date = Field(description="Trip start date")
    trip_end_date: date = Field(description="Trip end date")
    total_days: int = Field(description="Total number of days for the trip")
    daily_itinerary: List[DailyItinerary] = Field(
        description="Day-by-day itinerary details for the entire trip"
    )
    notes: Optional[str] = Field(description="General notes or preferences for the trip")
    
@CrewBase
class TripPlanner():
    """TripPlanner crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def tourism_agent(self) -> Agent:
        return Agent(config = self.agents_config['tourism_agent'], tools=[SerperDevTool()], verbose= True,)

    @agent
    def itinerary_planner(self) -> Agent:
        return Agent(config = self.agents_config['itinerary_planner'], tools=[SerperDevTool()], verbose= True,)

    @task
    def find_trip_locations(self) -> Task:
        return Task(config = self.tasks_config['find_trip_locations'], output_pydantic=TripLocationList,)

    @task
    def plan_itinerary(self) -> Task:
        return Task(config = self.tasks_config['plan_itinerary'],output_pydantic=TripItinerary, )

    @crew
    def crew(self) -> Crew:

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
