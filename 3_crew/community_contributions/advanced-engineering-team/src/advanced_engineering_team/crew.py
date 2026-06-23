import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from .llm import create_llm
from .tools import DockerCodeExecutor

callbacks = []
_lf_public = os.environ.get("LANGFUSE_PUBLIC_KEY")
_lf_secret = os.environ.get("LANGFUSE_SECRET_KEY")
if _lf_public and _lf_secret:
    try:
        from langfuse.callback import CallbackHandler
        callbacks.append(CallbackHandler())
    except ImportError:
        pass


@CrewBase
class AdvancedEngineeringTeam():
    """Multi-agent engineering team with per-role LLM configuration."""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],
            llm=create_llm("engineering_lead"),
            verbose=True,
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            llm=create_llm("backend_engineer"),
            verbose=True,
            tools=[DockerCodeExecutor()],
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            llm=create_llm("frontend_engineer"),
            verbose=True,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            llm=create_llm("test_engineer"),
            verbose=True,
            tools=[DockerCodeExecutor()],
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task']
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task']
        )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task']
        )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task']
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            callbacks=callbacks,
        )
