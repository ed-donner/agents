
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class DebateCrew:
    """Crew that conducts and judges a debate."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def proposer(self) -> Agent:
        return Agent(
            config=self.agents_config["proposer"],
            verbose=True,
        )

    @agent
    def opposer(self) -> Agent:
        return Agent(
            config=self.agents_config["opposer"],
            verbose=True,
        )

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config["judge"],
            verbose=True,
        )

    @task
    def propose(self) -> Task:
        return Task(
            config=self.tasks_config["propose"],
        )

    @task
    def oppose(self) -> Task:
        return Task(
            config=self.tasks_config["oppose"],
        )

    @task
    def decide(self) -> Task:
        return Task(
            config=self.tasks_config["decide"],
            context=[self.propose(), self.oppose()],
            output_file="debate_verdict.md",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
