from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List


@CrewBase
class IncidentPostmortem:
    """Blameless incident postmortem crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def incident_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config["incident_summarizer"],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def root_cause_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["root_cause_analyst"],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def action_owner(self) -> Agent:
        return Agent(
            config=self.agents_config["action_owner"],  # type: ignore[index]
            verbose=True,
        )

    @task
    def summarize_incident_task(self) -> Task:
        return Task(
            config=self.tasks_config["summarize_incident_task"],  # type: ignore[index]
        )

    @task
    def analyze_root_cause_task(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_root_cause_task"],  # type: ignore[index]
        )

    @task
    def finalize_postmortem_task(self) -> Task:
        return Task(
            config=self.tasks_config["finalize_postmortem_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
