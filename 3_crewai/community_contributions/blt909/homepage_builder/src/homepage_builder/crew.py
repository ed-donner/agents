from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel
from typing import List
from crewai_tools import SerperDevTool, FirecrawlScrapeWebsiteTool
from .tools.write_html_tool import WriteHtmlTool
from .tools.read_html_tool import ReadHtmlTool


class Business(BaseModel):
    name: str
    url: str
    sector: str

class BusinessList(BaseModel):
    businesses: List[Business]


@CrewBase
class ResearcherCrew():
    """ResearcherCrew – finds local businesses."""
    agents_config = 'config/researcher_agents.yaml'
    tasks_config = 'config/researcher_tasks.yaml'

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], # type: ignore[index]
            tools=[SerperDevTool()],
            verbose=True
        )

    @task
    def researcher_task(self) -> Task:
        return Task(
            config=self.tasks_config['researcher_task'], # type: ignore[index]
            output_pydantic=BusinessList
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


@CrewBase
class ScraperCrew():
    """ScraperCrew – scrapes a single business homepage."""
    agents_config = 'config/scraper_agents.yaml'
    tasks_config = 'config/scraper_tasks.yaml'

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['scraper'], # type: ignore[index]
            tools=[FirecrawlScrapeWebsiteTool()],
            verbose=True,
        )

    @task
    def scraper_task(self) -> Task:
        return Task(
            config=self.tasks_config['scraper_task'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


@CrewBase
class BuildAndReviewCrew():
    """BuildAndReviewCrew – designs, builds, reviews, and amends a homepage for one business."""
    agents_config = 'config/build_review_agents.yaml'
    tasks_config = 'config/build_review_tasks.yaml'

    agents: list[BaseAgent]
    tasks: list[Task]

    def _manager(self) -> Agent:
        return Agent(
            config=self.agents_config['manager'], # type: ignore[index]
            allow_delegation=True,
            verbose=True,
        )

    @agent
    def web_designer(self) -> Agent:
        return Agent(
            config=self.agents_config['web_designer'], # type: ignore[index]
            verbose=True,
        )

    @agent
    def frontend_developer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_developer'], # type: ignore[index]
            tools=[WriteHtmlTool()],
            verbose=True,
        )

    @agent
    def technical_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['technical_reviewer'], # type: ignore[index]
            tools=[ReadHtmlTool()],
            verbose=True,
        )

    @agent
    def accessibility_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['accessibility_reviewer'], # type: ignore[index]
            tools=[ReadHtmlTool()],
            verbose=True,
        )

    @task
    def web_designer_task(self) -> Task:
        return Task(
            config=self.tasks_config['web_designer_task'], # type: ignore[index]
        )

    @task
    def frontend_developer_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_developer_task'], # type: ignore[index]
        )

    @task
    def tech_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['tech_review_task'], # type: ignore[index]
            output_file='output/{name}_tech_review.md',
        )

    @task
    def accessibility_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['accessibility_review_task'], # type: ignore[index]
            output_file='output/{name}_accessibility_review.md',
        )

    @task
    def amend_design_task(self) -> Task:
        return Task(
            config=self.tasks_config['amend_design_task'], # type: ignore[index]
            context=[self.tech_review_task(), self.accessibility_review_task()]
        )

    @task
    def amend_html_task(self) -> Task:
        return Task(
            config=self.tasks_config['amend_html_task'], # type: ignore[index]
            context=[self.amend_design_task()]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self._manager(),
            memory=True,
            verbose=True,
        )
