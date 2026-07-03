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


class Summary(BaseModel):
    code_generated: str
    is_correct: bool
    needs_correction: bool
    changes_to_be_made: str
    code_summary: str


@CrewBase
class SoftwareEngineer:
    """Software Wngineer"""

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config: "config/agents.yaml"
    tasks_config: "config/tasks.yaml"

    def __init__(
        self,
        output_file_name: str,
        *args,
        **kwargs
    ):
        super().__init__(
            *args, **kwargs
        )
        self.output_file_name = output_file_name

    @agent
    def software_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config[
                "software_engineer"
            ],
            allow_code_execution=False,
            llm=LLM(
                model="gpt-4o",
                temperature=0
            )
        )
    
    @agent
    def tech_lead(self) -> Agent:
        return Agent(
            config=self.agents_config[
                "tech_lead"
            ],
            allow_code_execution=False,
            llm=LLM(
                model="claude-sonnet-4-20250514",
                temperature=0
            )
        )
    
    @agent
    def code_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config[
                "code_summarizer"
            ],
            allow_code_execution=False,
            llm=LLM(
                model="gpt-4o",
                temperature=0
            )
        )
    
    @task
    def generate_code(self) -> Task:
        return Task(
            config=self.tasks_config[
                "generate_code"
            ],
            output_file=self.output_file_name
        )
    
    @task
    def review_code(self) -> Task:
        return Task(
            config=self.tasks_config[
                "review_code"
            ]
        )
    
    @task
    def summarize_code(self) -> Task:
        return Task(
            config=self.tasks_config[
                "summarize_code"
            ],
            output_pydantic=Summary
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_rpm=7
        )
