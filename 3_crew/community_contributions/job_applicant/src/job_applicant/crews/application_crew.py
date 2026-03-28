from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from ..models import TailoredResume, CoverLetter, ApplicationResult
from ..tools.file_writer_tool import FileWriterTool
from ..tools.job_apply_tool import JobApplyTool


@CrewBase
class ApplicationCrew():
    """Application crew: tailors resume, writes cover letter, and submits application for a single job."""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def resume_tailor(self) -> Agent:
        return Agent(
            config=self.agents_config['resume_tailor'],
            tools=[FileWriterTool()],
            verbose=True,
        )

    @agent
    def cover_letter_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['cover_letter_writer'],
            tools=[FileWriterTool()],
            verbose=True,
        )

    @agent
    def job_applicant(self) -> Agent:
        return Agent(
            config=self.agents_config['job_applicant'],
            tools=[JobApplyTool()],
            verbose=True,
        )

    @task
    def tailor_resume(self) -> Task:
        return Task(
            config=self.tasks_config['tailor_resume'],
        )

    @task
    def write_cover_letter(self) -> Task:
        return Task(
            config=self.tasks_config['write_cover_letter'],
        )

    @task
    def submit_application(self) -> Task:
        return Task(
            config=self.tasks_config['submit_application'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Application crew with sequential processing."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
