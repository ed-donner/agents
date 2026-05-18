from copy import deepcopy
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

AGENTS_YAML = "config/agents.yaml"
TASKS_YAML = "config/tasks.yaml"


def _load_yaml(relative_path: str) -> dict:
    path = Path(__file__).resolve().parent / relative_path
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


class Feature(BaseModel):
    """A representation of a broken down feature represented by module and class """
    module_name: str = Field("The module name in snake_case with a .py type")
    class_name:str = Field("The class name in PascalCase")
    requirements: str = Field("The requirements for the module")

class Features(BaseModel):
    """List of test cases """
    features: list[Feature] = Field(description="List of features")


def build_breakdown_crew() -> Crew:
    """
    Build the breakdown-only crew without @CrewBase, so CrewAI never maps the full tasks.yaml.
    """
    agents_config = _load_yaml(AGENTS_YAML)
    tasks_full = _load_yaml(TASKS_YAML)
    task_cfg = deepcopy(tasks_full["breakdown_task"])
    agent_name = task_cfg.pop("agent")
    architect = Agent(config=agents_config[agent_name], verbose=True)
    breakdown_task = Task(
        config=task_cfg,
        agent=architect,
        output_pydantic=Features,
    )
    return Crew(
        agents=[architect],
        tasks=[breakdown_task],
        process=Process.sequential,
        verbose=True,
    )


def build_integration_crew() -> Crew:
    """Build the integration_task-only crew without @CrewBase, so CrewAI never maps the full tasks.yaml"""
    agents_config = _load_yaml(AGENTS_YAML)
    tasks_full = _load_yaml(TASKS_YAML)
    task_cfg = deepcopy(tasks_full["integration_task"])
    agent_name = task_cfg.pop("agent")
    engineer = Agent(config=agents_config[agent_name], verbose=True)
    integration_task = Task(config=task_cfg, agent=engineer)
    return Crew(
        agents=[engineer],
        tasks=[integration_task],
        process=Process.sequential,
        verbose=True,
    )


class TestCase(BaseModel):
    """ A module's test case """
    id: str = Field(description="Company name")
    title: str = Field(description="Stock ticker symbol")
    preconditions: str = Field(description="Reason this company is trending in the news")
    steps: str = Field(description="Steps to test")
    expected_result:str = Field(description="The expected result")
    target_method: str = Field(description="Which method in design to target with test")

class TestCasesList(BaseModel):
    """List of test cases """
    test_cases: list[TestCase] = Field(description="List of test cases")

class TestExecutionResult(BaseModel):
    """Test execution resul"""
    unit_test_name: str = Field(description="Unit test name")
    test_case_id: str = Field(description="Test case id if found")
    result: bool = Field(description="Whether test (true or false) ")
    details: str = Field(description="Test failure details is any")
    
class TestExecutionResults(BaseModel):
    """List of test results for a module """
    test_results: list[TestExecutionResult] = Field(description="Results of a test execution run")


FEATURE_ENGINEERING_TASK_KEYS = [
    "design_task",
    "write_test_cases_task",
    "code_task",
    "frontend_task",
    "test_task",
    "execute_unit_tests_task",
]

_FEATURE_TASK_PYDANTIC = {
    "write_test_cases_task": TestCasesList,
    "execute_unit_tests_task": TestExecutionResults,
}


def _feature_before_kickoff(inputs):
    print(f"Before kickoff function with inputs: {inputs}")
    return inputs


def _feature_after_kickoff(result):
    print(f"After kickoff function with result: {result}")
    return result


def build_feature_engineering_crew() -> Crew:
    """
    Build the feature-engineering crew without @CrewBase.
    """
    agents_config = _load_yaml(AGENTS_YAML)
    tasks_full = _load_yaml(TASKS_YAML)

    engineering_lead = Agent(config=agents_config["engineering_lead"], verbose=True)
    qa_test_design_lead = Agent(config=agents_config["qa_test_design_lead"], verbose=True)
    backend_engineer = Agent(
        config=agents_config["backend_engineer"],
        verbose=True,
        allow_code_execution=True,
        code_execution_mode="safe",
        max_execution_time=500,
        max_retry_limit=3,
    )
    frontend_engineer = Agent(config=agents_config["frontend_engineer"], verbose=True)
    test_engineer = Agent(
        config=agents_config["test_engineer"],
        verbose=True,
        allow_code_execution=True,
        code_execution_mode="safe",
        max_execution_time=500,
        max_retry_limit=3,
    )
    test_automation_engineer = Agent(
        config=agents_config["test_automation_engineer"],
        verbose=True,
        allow_code_execution=True,
        code_execution_mode="safe",
        max_execution_time=500,
        max_retry_limit=3,
    )

    agents_by_yaml_key = {
        "engineering_lead": engineering_lead,
        "qa_test_design_lead": qa_test_design_lead,
        "backend_engineer": backend_engineer,
        "frontend_engineer": frontend_engineer,
        "test_engineer": test_engineer,
        "test_automation_engineer": test_automation_engineer,
    }

    built_tasks: dict[str, Task] = {}
    ordered_tasks: list[Task] = []

    for task_key in FEATURE_ENGINEERING_TASK_KEYS:
        task_cfg = deepcopy(tasks_full[task_key])
        agent_key = task_cfg.pop("agent")
        context_names = task_cfg.pop("context", None) or []

        context_tasks = [built_tasks[name] for name in context_names]
        agent = agents_by_yaml_key[agent_key]

        kwargs: dict = {
            "config": task_cfg,
            "agent": agent,
        }
        if context_tasks:
            kwargs["context"] = context_tasks
        if task_key in _FEATURE_TASK_PYDANTIC:
            kwargs["output_pydantic"] = _FEATURE_TASK_PYDANTIC[task_key]

        task_obj = Task(**kwargs)
        built_tasks[task_key] = task_obj
        ordered_tasks.append(task_obj)

    crew = Crew(
        agents=list(agents_by_yaml_key.values()),
        tasks=ordered_tasks,
        process=Process.sequential,
        verbose=True,
    )
    crew.before_kickoff_callbacks.append(_feature_before_kickoff)
    crew.after_kickoff_callbacks.append(_feature_after_kickoff)
    return crew
