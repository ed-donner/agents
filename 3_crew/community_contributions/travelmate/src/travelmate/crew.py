from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class Travelmate():
    """Travelmate crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    
    @agent
    def travel_guide_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['travel_guide_agent'], 
            verbose=True
        )

    @agent
    def food_guide_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['food_guide_agent'],
            verbose=True
        )

    @agent
    def stay_guide_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['stay_guide_agent'],
            verbose=True
        )    

    @agent
    def travel_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['travel_planner_agent'],
            verbose=True
        )
        
    @agent
    def activity_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['activity_planner_agent'], 
            verbose=True
        )
        
    @agent
    def food_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['food_planner_agent'], 
            verbose=True
        )    

    @agent
    def budget_planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['budget_planner_agent'],
            verbose=True
        )

    @task
    def travel_guide_task(self) -> Task:
        return Task(
            config=self.tasks_config['travel_guide_task']
        )

    @task
    def food_guide_task(self) -> Task:
        return Task(
            config=self.tasks_config['food_guide_task']
        )

    @task
    def stay_guide_task(self) -> Task:
        return Task(
            config=self.tasks_config['stay_guide_task']
        )

    @task
    def travel_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['travel_plan_task']
        )

    @task
    def activity_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['activity_plan_task']
        )

    @task
    def food_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['food_plan_task']
        )

    @task
    def budget_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['budget_plan_task'] 
        )

    @task
    def complete_travel_package_task(self) -> Task:
        return Task(
            config=self.tasks_config['complete_travel_package_task'], 
            output_file='output/complete_travel_package_{location}.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Travelmate crew"""
        return Crew(
            agents=self.agents, 
            tasks=[self.complete_travel_package_task()], 
            process=Process.sequential,
            verbose=True
        )
