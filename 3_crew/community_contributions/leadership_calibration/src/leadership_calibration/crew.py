from tabnanny import verbose
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class LeadershipCalibration():
    """Leadership Calibration crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    """
    Crew responsible for orchestrating a structured debate between:
    - Senior Software Architect
    - Engineering Manager

    Topic:
    Optimal balance between technical skills and people management focus.
    """

    # Load agents from agents.yaml
    agents_config = "config/agents.yaml"

    # Load tasks from tasks.yaml
    tasks_config = "config/tasks.yaml"

    #
    # AGENTS
    #
    @agent
    def senior_architect_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['senior_architect_agent'],
            verbose=True
        )

    @agent
    def engineering_manager_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["engineering_manager_agent"],
            verbose=True
        )

    #
    # TASKS
    #
    @task
    def architect_position_statement(self) -> Task:
        return Task(
            config=self.tasks_config["architect_position_statement"]
        )

    @task
    def engineering_manager_position_statement(self) -> Task:
        return Task(
            config=self.tasks_config["engineering_manager_position_statement"]
        )

    @task
    def final_alignment_and_resolution(self) -> Task:
        return Task(
            config=self.tasks_config["final_alignment_and_resolution"]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
