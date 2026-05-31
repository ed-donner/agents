import os
from functools import partial

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, before_kickoff, crew, task

from engineering_team.callbacks import on_architecture_complete
from engineering_team.models import SystemArchitecture


def openrouter_llm(model_env, default_model):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is required")
    headers = {}
    referer = os.getenv("OPENROUTER_HTTP_REFERER")
    title = os.getenv("OPENROUTER_TITLE")
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-OpenRouter-Title"] = title
    kwargs = {
        "model": os.getenv(model_env, default_model),
        "api_key": api_key,
        "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    }
    if headers:
        kwargs["extra_headers"] = headers
    return LLM(**kwargs)


@CrewBase
class EngineeringTeam:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @before_kickoff
    def prepare_inputs(self, inputs):
        current = getattr(self, "runtime", {})
        self.runtime = {
            "crew": current.get("crew"),
            "architecture_task": current.get("architecture_task"),
            "inputs": inputs,
            "architecture": None,
            "modules_by_name": {},
            "completed_modules": set(),
            "scheduled_modules": set(),
            "module_tasks": {},
            "final_task_created": False,
        }
        return inputs

    @agent
    def system_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["system_architect"],
            verbose=True,
            llm=openrouter_llm("OPENROUTER_ARCHITECT_MODEL", "openrouter/openai/gpt-4o"),
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_engineer"],
            verbose=True,
            llm=openrouter_llm("OPENROUTER_ENGINEER_MODEL", "openrouter/anthropic/claude-3.7-sonnet"),
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=500,
            max_retry_limit=3,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["test_engineer"],
            verbose=True,
            llm=openrouter_llm("OPENROUTER_ENGINEER_MODEL", "openrouter/anthropic/claude-3.7-sonnet"),
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=500,
            max_retry_limit=3,
        )

    @agent
    def integration_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["integration_engineer"],
            verbose=True,
            llm=openrouter_llm("OPENROUTER_ENGINEER_MODEL", "openrouter/anthropic/claude-3.7-sonnet"),
        )

    @task
    def architecture_task(self) -> Task:
        return Task(
            name="architecture_task",
            config=self.tasks_config["architecture_task"],
            output_pydantic=SystemArchitecture,
            callback=partial(on_architecture_complete, self),
        )

    @crew
    def crew(self) -> Crew:
        crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
        if not hasattr(self, "runtime"):
            self.runtime = {}
        self.runtime["crew"] = crew
        self.runtime["architecture_task"] = self.tasks[0]
        return crew
