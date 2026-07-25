from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Crew definition
# ---------------------------------------------------------------------------

@CrewBase
class DigitalFarmTeam:
    """DigitalFarmTeam crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def database_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["database_architect"],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=240,
            max_retry_limit=3,
        )

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(config=self.agents_config['engineering_lead'], verbose=True)

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'], # type: ignore[index]
            verbose=True, allow_code_execution=True, code_execution_mode="safe", max_execution_time=240, max_retry_limit=5
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(config=self.agents_config['frontend_engineer'], verbose=True)

    @agent
    def test_engineer(self) -> Agent:
        return Agent(config=self.agents_config['test_engineer'], 
        verbose=True, allow_code_execution=True, code_execution_mode="safe", max_execution_time=240, max_retry_limit=5
    )


    @task
    def design_task(self) -> Task:
        return Task(config=self.tasks_config['design_task'])

    @task
    def coding_task(self) -> Task:
        return Task(config=self.tasks_config['coding_task'])

    @task
    def frontend_task(self) -> Task:
        return Task(config=self.tasks_config['frontend_task'])

    @task
    def test_task(self) -> Task:
        return Task(config=self.tasks_config['test_task'])

    @task
    def database_task(self) -> Task:
        return Task(config=self.tasks_config["database_task"])


    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )


