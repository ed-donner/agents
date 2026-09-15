from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from .tools.sandbox_tools import sandbox_tools
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class EngineeringTeam():
    """EngineeringTeam crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # The engineering lead is the dedicated manager, not a worker agent.
    def engineering_lead(self) -> Agent:
        # The first hierarchical run took a long time and made many repeated
        # tool calls, so the manager needs explicit iteration and time limits.
        return Agent(
            config=self.agents_config['engineering_lead'],
            verbose=True,
            allow_delegation=True,
            max_iter=12,
            max_execution_time=600,
            max_retry_limit=1,
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            tools=sandbox_tools,
            max_iter=10,
            max_execution_time=300,
            max_retry_limit=1,
        )

    @agent
    def code_quality_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['code_quality_reviewer'],
            verbose=True,
            tools=sandbox_tools,
            max_iter=10,
            max_execution_time=300,
            max_retry_limit=1,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True,
            tools=sandbox_tools,
            mcps=["https://mcp.context7.com/mcp"],
            max_iter=10,
            max_execution_time=300,
            max_retry_limit=1,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            verbose=True,
            tools=sandbox_tools,
            max_iter=10,
            max_execution_time=300,
            max_retry_limit=1,
        )

    @agent
    def qa_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['qa_engineer'],
            verbose=True,
            tools=sandbox_tools,
            max_iter=10,
            max_execution_time=300,
            max_retry_limit=1,
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task']
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'],
        )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'],
        )

    @task
    def code_quality_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_quality_task'],
        )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],
        )

    @task
    def qa_task(self) -> Task:
        return Task(
            config=self.tasks_config['qa_task'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the EngineeringTeam crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        manager = self.engineering_lead()

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.hierarchical,
            manager_agent=manager,
            verbose=True,
            tracing=True,
        )
