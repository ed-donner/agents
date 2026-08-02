from crewai import (
    Agent,
    Crew,
    Process,
    Task,
    LLM
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


class TechLeadReview(BaseModel):
    is_correct: bool
    needs_correction: bool
    changes_to_be_made: str


@CrewBase
class TechLead:
    """Tech Lead"""

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config: "config/tech_lead_agent.yaml"
    tasks_config: "config/tech_lead_task.yaml"

    @agent
    def tech_lead(self) -> Agent:
        return Agent(
            config=self.agents_config[
                "tech_lead"
            ],
            allow_code_execution=False,
            llm=LLM(
                model="claude-sonnet-4-20250514",
                temperature=0,
                max_tokens=10000000,
                stream=True
            )
        )
    
    @task
    def review_code(self) -> Task:
        return Task(
            config=self.tasks_config[
                "review_code"
            ],
            output_pydantic=TechLeadReview
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True
        )