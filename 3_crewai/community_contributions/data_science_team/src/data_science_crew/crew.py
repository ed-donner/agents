from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from .tools.sandbox_tools import sandbox_tools
import data_science_crew.patch  # Apply MCP patch side effect


@CrewBase
class DataScienceCrew():
    """DataScienceCrew crew for Full End-to-End Execution"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def data_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['data_strategist'],
            verbose=True,
            tools=sandbox_tools
        )

    @agent
    def data_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['data_engineer'],
            verbose=True,
            tools=sandbox_tools
        )

    @agent
    def dashboard_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['dashboard_engineer'],
            verbose=True,
            tools=sandbox_tools,
            mcps=["https://mcp.context7.com/mcp"]
        )

    @agent
    def qa_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config['qa_reporter'],
            verbose=True,
            tools=sandbox_tools
        )

    @task
    def strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config['strategy_task']
        )

    @task
    def data_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_task']
        )

    @task
    def dashboard_task(self) -> Task:
        return Task(
            config=self.tasks_config['dashboard_task']
        )

    @task
    def report_task(self) -> Task:
        return Task(
            config=self.tasks_config['report_task']
        )

    @crew
    def crew(self) -> Crew:
        """Creates the DataScienceCrew crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            tracing=True
        )
