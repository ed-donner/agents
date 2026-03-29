from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from ..models import CandidateProfile, JobMatchList
from ..tools.resume_parser_tool import ResumeParserTool
from ..tools.job_search_tool import JobSearchTool


@CrewBase
class ResearchCrew():
    """Research crew: parses resume, searches jobs, and matches candidates to postings."""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    resume_path: str = ""

    @agent
    def resume_parser(self) -> Agent:
        return Agent(
            config=self.agents_config['resume_parser'],
            tools=[ResumeParserTool(resume_path=self.resume_path)],
            verbose=True,
        )

    @agent
    def job_searcher(self) -> Agent:
        return Agent(
            config=self.agents_config['job_searcher'],
            tools=[JobSearchTool()],
            verbose=True,
        )

    @agent
    def job_matcher(self) -> Agent:
        return Agent(
            config=self.agents_config['job_matcher'],
            tools=[],
            verbose=True,
        )

    @task
    def parse_resume(self) -> Task:
        return Task(
            config=self.tasks_config['parse_resume'],
            output_pydantic=CandidateProfile,
        )

    @task
    def search_jobs(self) -> Task:
        return Task(
            config=self.tasks_config['search_jobs'],
        )

    @task
    def match_jobs(self) -> Task:
        return Task(
            config=self.tasks_config['match_jobs'],
            output_pydantic=JobMatchList,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research crew with sequential processing."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
