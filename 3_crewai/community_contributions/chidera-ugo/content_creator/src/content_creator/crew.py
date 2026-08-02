from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool


@CrewBase
class ContentCreator():
    """Content Creator crew — research, write, edit, and SEO-optimize a blog post."""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            tools=[SerperDevTool()],
            verbose=True,
        )

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config['writer'],
            verbose=True,
        )

    @agent
    def editor(self) -> Agent:
        return Agent(
            config=self.agents_config['editor'],
            verbose=True,
        )

    @agent
    def seo_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['seo_strategist'],
            verbose=True,
        )

    @task
    def research_topic(self) -> Task:
        return Task(
            config=self.tasks_config['research_topic'],
        )

    @task
    def write_draft(self) -> Task:
        return Task(
            config=self.tasks_config['write_draft'],
        )

    @task
    def edit_draft(self) -> Task:
        return Task(
            config=self.tasks_config['edit_draft'],
        )

    @task
    def optimize_seo(self) -> Task:
        return Task(
            config=self.tasks_config['optimize_seo'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ContentCreator crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
