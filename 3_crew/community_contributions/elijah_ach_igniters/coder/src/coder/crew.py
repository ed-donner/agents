from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class Coder():
    """Coder crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

   
    @agent
    def coder(self) -> Agent:
        return Agent(
            config=self.agents_config['coder'], # type: ignore[index]
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="unsafe",  # Uses Docker for safety
            max_execution_time=30, 
            max_retry_limit=3 
        )


    @task
    def coding_task(self) -> Task:
        return Task(
            config=self.tasks_config['coding_task'], # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Coder crew"""
        

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
