from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from litellm import Field
from pydantic import BaseModel
import datetime

class CodeReviewFeedback(BaseModel):
    code_being_reviewed: str = Field(description="the snippet of code being reviewed")
    review_comments_markdown: str = Field(description="Review comments in markdown format")
    review_timestamp: datetime.datetime = Field(description="Timestamp when review was performed")
    passed_review: bool = Field(description="Does the code pass your review or not?")


@CrewBase
class EngineeringCrew():
    """EngineeringCrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "./config/agents.yaml"
    tasks_config = "./config/tasks.yaml"

    @agent
    def development_lead(self) -> Agent:
        return Agent(config=self.agents_config["development_lead"], verbose=True)  # type: ignore[index]
    
    @agent
    def backend_engineer(self) -> Agent:
        return Agent(config=self.agents_config["backend_engineer"], verbose=True) # type: ignore[index]

    @agent
    def code_reviewer(self) -> Agent:
        return Agent(config=self.agents_config["code_reviewer"], verbose=True, output_pydantic= CodeReviewFeedback) # type: ignore[index]
    
    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(config=self.agents_config["frontend_engineer"], verbose=True) # type: ignore[index]

    @agent
    def test_engineer(self) -> Agent:
        return Agent(config=self.agents_config["test_engineer"], verbose=True) # type: ignore[index]

    @task
    def design_task(self) -> Task:
        return Task(config=self.tasks_config["design_task"], verbose=True)  # type: ignore[index]

    @task
    def backend_coding_task(self) -> Task:
        return Task(config=self.tasks_config["backend_coding_task"], verbose=True) # type: ignore[index]

    @task
    def code_review_task(self) -> Task:
        return Task(config=self.tasks_config["code_review_task"], verbose=True, output_pydantic=CodeReviewFeedback) # type: ignore[index]

    @task
    def frontend_code_review_task(self) -> Task:
        return Task(config=self.tasks_config["frontend_code_review_task"], verbose=True, output_pydantic=CodeReviewFeedback) # type: ignore[index]

    @task
    def test_preparation_task(self) -> Task:
        return Task(config=self.tasks_config["test_preparation_task"], verbose=True) # type: ignore[index]

    @task
    def frontend_coding_task(self) -> Task:
        return Task(config=self.tasks_config["frontend_coding_task"], verbose=True) # type: ignore[index]

    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @agent decorator,
            process=Process.sequential,
            verbose=True,
        )

