from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from resume_match_ai.tools.custom_tool import download_resume, extract_resume

# file_reader = FileReadTool()

@CrewBase
class ResumeMatchAi():
    """ResumeMatchAi crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def resume_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['resume_analyst'], # type: ignore[index]
            verbose=True,
            tools=[download_resume, extract_resume]
        )

    @agent
    def job_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['job_scraper'], # type: ignore[index]
            verbose=True,
            tools=[extract_resume]
        )

    @agent
    def matchmaker(self) -> Agent:
        return Agent(
            config=self.agents_config['matchmaker'], # type: ignore[index]
            verbose=True,
            tools=[extract_resume]
        )

    @agent
    def advisor(self) -> Agent:
        return Agent(
            config=self.agents_config['advisor'], # type: ignore[index]
            verbose=True,
            tools=[extract_resume]
        )


    @task
    def resume_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['resume_analysis_task'], # type: ignore[index]
            output_file='output/analyst_report.md'
        )

    @task
    def job_scraping_task(self) -> Task:
        return Task(
            config=self.tasks_config['job_scraping_task'], # type: ignore[index]
            output_file='output/job_scraping_report.md'
        )

    @task
    def job_matching_task(self) -> Task:
        return Task(
            config=self.tasks_config['job_matching_task'], # type: ignore[index]
            output_file='output/job_matching_report.md'
        )

    @task
    def resume_advising_task(self) -> Task:
        return Task(
            config=self.tasks_config['resume_advising_task'], # type: ignore[index]
            output_file='output/resume_advising_report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ResumeMatchAi crew"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
