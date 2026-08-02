from typing import Tuple, Any

from crewai import Agent, Crew, Process, Task, TaskOutput
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class MarketResearcher():
    """MarketResearcher crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools

    @agent
    def research_director(self) -> Agent:
        return Agent(
            config=self.agents_config['research_director'], # type: ignore[index]
            verbose=True,
            allow_delegation=True
        )

    @agent
    def market_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['market_researcher'], # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def strategic_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['strategic_analyst'], # type: ignore[index]
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_competitor_a(self) -> Task:
        return Task(
            config=self.tasks_config['research_competitor_a'], # type: ignore[index]
            async_execution=True
        )

    @task
    def research_competitor_b(self) -> Task:
        return Task(
            config=self.tasks_config['research_competitor_b'], # type: ignore[index]
            async_execution=True
        )

    @task
    def research_competitor_c(self) -> Task:
        return Task(
            config=self.tasks_config['research_competitor_c'], # type: ignore[index]
            async_execution=True
        )

    @task
    def research_market_trends(self) -> Task:
        return Task(
            config=self.tasks_config['research_market_trends'], # type: ignore[index]
            async_execution=True
        )

    def validate_report_content(self, result: TaskOutput) -> Tuple[bool, Any]:
        """Validate report content meets requirements."""
        try:
            # Check word count
            word_count = len(result.raw.split())
            if word_count > 1200:
                return (False, "Report exceeds 1200 words")
        except Exception as e:
            return (False, f"Unexpected error during validation: {e}")
        return (True, result)

    @task
    def synthesize_report(self) -> Task:
        return Task(
            config=self.tasks_config['synthesize_report'], # type: ignore[index]
            guardrails=[
                self.validate_report_content,
                "The writing style should be professional, empirical, and engaging. It is meant for the C-level business audience."
            ],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the MarketResearcher crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=[self.market_researcher(), self.strategic_analyst()], # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.hierarchical,
            manager_agent=self.research_director(),
            verbose=True
        )
