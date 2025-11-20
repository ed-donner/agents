from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel
from typing import List


class BusinessUseCase(BaseModel):
    business_use_case: str


@CrewBase
class BusinessCrew:
    """Business Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def business_personal(self) -> Agent:
        return Agent(
            config=self.agents_config["business_personal"],
            allow_delegation=True
        )
    
    @task
    def business_usecase_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config["business_usecase_generation_task"],
            output_pydantic=BusinessUseCase
        )
    
    def track_collaboration_from_business(self, output):
        """Track collaboration patterns"""
        print(f"output from stepcallback: {output}")

    @crew
    def crew(self) -> Crew:
        """Creates the Business Crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            step_callback=self.track_collaboration_from_business,
            memory=True
        )
