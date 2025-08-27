import json
from crewai import Agent, Crew, Process, Task, TaskOutput
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import Any, List, Tuple
from crewai_tools import SerperDevTool
from pydantic import BaseModel

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


from pydantic import BaseModel

class Research(BaseModel):
    title: str
    content: str


def validate_json_output(result: TaskOutput) -> Tuple[bool, Any]:
    """Validate and parse JSON output."""
    try:
        # Try to parse as JSON
        result
        data = json.loads(result.raw)
        return (True, data)
    except json.JSONDecodeError as e:
        return (False, "Invalid JSON format")

def validate_report_content(result: TaskOutput) -> Tuple[bool, Any]:
    """Validate report content meets requirements."""
    try:
        # Check word count
        word_count = len(result.raw.split())
        if word_count > 500:
            return (False, "Report exceeds 500 words")
        # Additional validation logic here   
        return (True, result)
    except Exception as e:
        return (False, "Unexpected error during validation")


@CrewBase
class FinancialResearcherGuard():
    """FinancialResearcherGuard crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'], # type: ignore[index]
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> TaskOutput:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
#            agent=researcher,
            output_json=Research,
            guardrail=validate_json_output,
            max_retries=2 
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'], # type: ignore[index]
            output_file='output/report.md',
            guardrail=validate_report_content,
            max_retries=2 
        )

    @crew
    def crew(self) -> Crew:
        """Creates the FinancialResearcherGuard crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
