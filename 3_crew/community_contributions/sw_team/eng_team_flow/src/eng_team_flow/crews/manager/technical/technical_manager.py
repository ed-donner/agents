from crewai import (
    Agent,
    Crew,
    Process,
    Task
)
from crewai.project import (
    CrewBase,
    agent,
    crew,
    task
)
from crewai.agents.agent_builder.base_agent import (
    BaseAgent
)
from pydantic import (
    BaseModel
)
from typing import List


class EngineeringDesignTask(BaseModel):
    task_name: str
    task_description: str

    
class EngineeringDesignTaskList(BaseModel):
    tasks: list[EngineeringDesignTask]
    provide_more_clarity: str = ""
    clarification_query: str = ""
    additional_implementation_details: str = ""


@CrewBase
class TechnicalManagerCrew:
    """Technical Manager Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config: "config/agents.yaml"
    tasks_config: "config/tasks.yaml"

    @agent
    def technical_manager(self) -> Agent:
        return Agent(
            config=self.agents_config[
                "technical_manager"
            ],
            allow_delegation=True
        )

    @task
    def generate_engineering_task_list(self) -> Task:
        return Task(
            config=self.tasks_config[
                "generate_engineering_task_list"
            ],
            output_pydantic=EngineeringDesignTaskList
        )
    
    def track_collaboration_from_manager(self, output):
        """Track collaboration patterns"""
        print(f"output from stepcallback: {output}")

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            step_callback=self.track_collaboration_from_manager,
            memory=True
        )