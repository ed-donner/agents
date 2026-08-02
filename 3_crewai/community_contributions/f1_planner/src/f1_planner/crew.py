from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import SerperDevTool
from .tools.tools import GoogleFlightsTool, GoogleHotelsPriceTool, CurrencyExchangeTool
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class F1Planner():
    """F1Planner crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def travel_logistics_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['travel_logistics_agent'],
            tools=[SerperDevTool(), GoogleFlightsTool(), GoogleHotelsPriceTool()],
            max_iter=15,
            verbose=True
        )

    @agent
    def f1_experience_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['f1_experience_strategist'],
            tools=[SerperDevTool(), CurrencyExchangeTool()],
            max_iter=20,
            verbose=True
        )

    @agent
    def budget_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['budget_planner_agent'],
            verbose=True
        )
    
    @agent
    def local_guide(self) -> Agent:
        return Agent(
            config=self.agents_config['local_guide'],
            tools=[SerperDevTool()],
            max_iter=25,
            verbose=True
        )
    
    @agent
    def master_planner(self) -> Agent:
        return Agent(
            config=self.agents_config['master_planner'],
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def flight_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['flight_research_task'], 
        )

    @task
    def accommodation_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['accommodation_research_task'], 
        )

    @task
    def f1_experience_strategist_task(self) -> Task:
        return Task(
            config=self.tasks_config['f1_experience_strategist_task'], 
        )

    @task
    def budget_planner_task(self) -> Task:
        return Task(
            config=self.tasks_config['budget_planner_task'], 
        )
    
    @task
    def local_guide_task(self) -> Task:
        return Task(
            config=self.tasks_config['local_guide_task'], 
        )
    
    @task
    def master_planner_task(self) -> Task:
        return Task(
            config=self.tasks_config['master_planner_task'], 
        )

    @crew
    def crew(self) -> Crew:
        """Creates the F1Planner crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
