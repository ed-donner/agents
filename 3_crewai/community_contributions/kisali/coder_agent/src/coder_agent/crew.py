from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class CoderAgent():
    """CoderAgent crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def python_coder_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['python_coder_agent'],
            verbose=True,
            code_execution_limit="safe",
            allow_code_execution=True,
            max_execution_time=30,
            max_retry_limit=3
        )

    @task
    def python_coding_task(self) -> Task:
        return Task(
            config=self.tasks_config['python_coding_task'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CoderAgent crew"""
    
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
