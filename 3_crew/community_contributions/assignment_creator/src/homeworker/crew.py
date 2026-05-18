import os
from crewai import Agent, Crew, Process, Task
from crewai_tools import FileReadTool

from .tools.sendgrid_tool import SendGridTool
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
load_dotenv()

file_read_tool = FileReadTool(base_path="output")

@CrewBase
class Homework():
    """Homework Helper Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def set_inputs(self, inputs: dict):
        self.topic = inputs.get("topic")
        self.grade = inputs.get("grade")
        self.to_email = inputs.get("to_email")

    # -------------------------
    # Agents
    # -------------------------

    @agent
    def maths_tutor(self) -> Agent:
        return Agent(config=self.agents_config['maths_tutor'], verbose=True)

    @agent
    def english_tutor(self) -> Agent:
        return Agent(config=self.agents_config['english_tutor'], verbose=True)

    @agent
    def general_tutor(self) -> Agent:
        return Agent(config=self.agents_config['general_tutor'], verbose=True)

    @agent
    def principal(self) -> Agent:
        return Agent(config=self.agents_config['principal'], verbose=True)

    @agent
    def mail_composer(self) -> Agent:
        return Agent(
            config=self.agents_config['mail_composer'],
            tools=[file_read_tool],
            verbose=True
        )

    @agent
    def mailer(self) -> Agent:
        return Agent(
            config=self.agents_config['mailer'],
            tools=[SendGridTool(), file_read_tool],
            memory=True,
            verbose=True
        )

    # -------------------------
    # Tasks
    # -------------------------

    @task
    def create_math_homework(self) -> Task:
        return Task(config=self.tasks_config['create_math_homework'])

    @task
    def create_english_homework(self) -> Task:
        return Task(config=self.tasks_config['create_english_homework'])

    @task
    def create_general_homework(self) -> Task:
        return Task(config=self.tasks_config['create_general_homework'])

    @task
    def compose_email(self) -> Task:
        return Task(config=self.tasks_config['compose_email'])

    @task
    def send_email(self) -> Task:
        return Task(config=self.tasks_config['send_email'], timeout=60)

    # -------------------------
    # MAIN CREW
    # -------------------------

    @crew
    def crew(self) -> Crew:
        """Main Homework Crew with principal routing inside the same crew."""

        # For dynamic routing, use main.py orchestration as now.
        crew = Crew(
            agents=[
                self.principal(),
                self.maths_tutor(),
                self.english_tutor(),
                self.general_tutor(),
                self.mail_composer(),
                self.mailer()
            ],
            tasks=[],  # No static tasks, since routing is handled in main.py
            process=Process.sequential,
            verbose=True
        )
        return crew