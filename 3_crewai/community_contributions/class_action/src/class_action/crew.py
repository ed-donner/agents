from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class ClassAction():
    """ClassAction crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def research_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['research_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def verifier_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['verifier_agent'], # type: ignore[index]
            verbose=True
        )
    
    @agent
    def summarizer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['summarizer_agent'], # type: ignore[index]
            verbose=True
        )

    @task
    def research_class_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_class_task'], # type: ignore[index]
        )

    @task
    def verify_class_task(self) -> Task:
        return Task(
            config=self.tasks_config['verify_class_task'], # type: ignore[index]
        )

    @task
    def summarize_class_task(self) -> Task:
        return Task(
            config=self.tasks_config['summarize_class_task'], # type: ignore[index]
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ClassAction crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
