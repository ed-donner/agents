from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool
from .tools.image_gen_tool import ImageGenerationTool


@CrewBase
class MarketingTeam():
    """MarketingTeam crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def marketing_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['marketing_lead'],
            tools=[SerperDevTool()],
            allow_delegation=True,
            verbose=True,
        )

    @agent
    def content_developer(self) -> Agent:
        return  Agent(
            config=self.agents_config['content_developer'],
            tools=[SerperDevTool()],
            verbose=True,
        )
    
    @agent
    def graphic_designer(self) -> Agent:
        return Agent(
            config=self.agents_config['graphic_designer'],
            tools=[ImageGenerationTool()],
            verbose=True,
        )

    @agent
    def social_media_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['social_media_manager'],
            verbose=True,
        )

    @task
    def strategy_task(self) -> Task:
        return Task(config=self.tasks_config['strategy_task'])

    @task
    def copy_task(self) -> Task:
        return Task(config=self.tasks_config['copy_task'])

    @task
    def design_task(self) -> Task:
        return Task(config=self.tasks_config['design_task'])

    @task
    def publish_task(self) -> Task:
        return Task(config=self.tasks_config['publish_task'])

    @crew
    def crew(self) -> Crew:
        """Creates the MarketingTeam crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
