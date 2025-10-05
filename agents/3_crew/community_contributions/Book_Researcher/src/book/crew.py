from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

@CrewBase
class BookResearchCrew():
    """Book market research crew"""

    @agent
    def trending_books_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['trending_books_agent'],
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def top_novelists_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['top_novelists_agent'],
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def genre_research_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['genre_research_agent'],
            verbose=True,
            tools=[SerperDevTool()]
        )

    @task
    def trending_topics_task(self) -> Task:
        return Task(
            config=self.tasks_config['trending_topics_task']
        )

    @task
    def top_novelists_task(self) -> Task:
        return Task(
            config=self.tasks_config['top_novelists_task']
        )

    @task
    def genre_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['genre_research_task']
        )

    @crew
    def crew(self) -> Crew:
        """Creates the research crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

