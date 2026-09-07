from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel
from typing import List

search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

class TopicWeightage(BaseModel):
    topic: str
    weightage_percent: int
    sample_questions: List[str]

class PrepGuide(BaseModel):
    company: str
    role: str
    round_breakdown: List[str]
    topic_weightage: List[TopicWeightage]
    one_week_plan: str
    must_know_questions: List[str]

@CrewBase
class InterviewPrepCrew():

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def company_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['company_researcher'], # type: ignore[index]
            tools=[search_tool, scrape_tool],
            max_retry_limit=3,
            verbose=True
        )

    @agent
    def interview_intel_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['interview_intel_agent'], # type: ignore[index]
            tools=[search_tool, scrape_tool],
            max_retry_limit=3,
            verbose=True
        )

    @agent
    def resource_curator(self) -> Agent:
        return Agent(
            config=self.agents_config['resource_curator'], # type: ignore[index]
            tools=[search_tool],
            max_retry_limit=3,
            verbose=True
        )

    @agent
    def interview_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['interview_strategist'], # type: ignore[index]
            verbose=True
        )

    @task
    def research_company_task(self) -> Task:
        return Task(config=self.tasks_config['research_company_task']) # type: ignore[index]

    @task
    def gather_questions_task(self) -> Task:
        return Task(config=self.tasks_config['gather_questions_task']) # type: ignore[index]

    @task
    def curate_resources_task(self) -> Task:
        return Task(config=self.tasks_config['curate_resources_task']) # type: ignore[index]

    @task
    def build_prep_guide_task(self) -> Task:
        return Task(
            config=self.tasks_config['build_prep_guide_task'], # type: ignore[index]
            output_pydantic=PrepGuide
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
