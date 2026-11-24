from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from product_factory.tools.sandbox_reset import validate_workstream_id, workstream_root
from product_factory.tools.sandbox_tools import make_sandbox_tools
from product_factory.tools.verdict import QualityVerdict


class ReportTask(Task):
    def prompt(self) -> str:
        return super().prompt().replace(
            "you MUST return the actual complete content as the final answer, not a summary.",
            "The final answer must be the complete report described above, with every named part.",
        )


@CrewBase
class ProductFactory:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    agents: list[BaseAgent]
    tasks: list[Task]

    def __init__(self, workstream_id: str = "main") -> None:
        self.workstream_id = validate_workstream_id(workstream_id)
        self.root = workstream_root(self.workstream_id)
        self.root.mkdir(parents=True, exist_ok=True)
        self.sandbox_tools = make_sandbox_tools(self.root)

    def engineering_lead(self) -> Agent:
        return Agent(config=self.agents_config["engineering_lead"])  # type: ignore[index]

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_engineer"],  # type: ignore[index]
            tools=self.sandbox_tools,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["frontend_engineer"],  # type: ignore[index]
            tools=self.sandbox_tools,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["test_engineer"],  # type: ignore[index]
            tools=self.sandbox_tools,
        )

    @agent
    def quality_inspector(self) -> Agent:
        inspector_tool_names = {
            "check_sandbox_app",
            "list_sandbox_files",
            "read_sandbox_file",
            "run_sandbox_python",
        }
        return Agent(
            config=self.agents_config["quality_inspector"],  # type: ignore[index]
            tools=[
                item
                for item in self.sandbox_tools
                if item.name in inspector_tool_names
            ],
        )

    @task
    def design_task(self) -> Task:
        return Task(
            description="Use the separately completed design pre-step:\n{design}",
            expected_output="The design supplied by the engineering lead.",
        )

    @task
    def backend_task(self) -> Task:
        return ReportTask(config=self.tasks_config["backend_task"])  # type: ignore[index]

    @task
    def frontend_task(self) -> Task:
        return ReportTask(config=self.tasks_config["frontend_task"])  # type: ignore[index]

    @task
    def test_task(self) -> Task:
        return ReportTask(config=self.tasks_config["test_task"])  # type: ignore[index]

    @task
    def quality_task(self) -> Task:
        return ReportTask(
            config=self.tasks_config["quality_task"],  # type: ignore[index]
            output_pydantic=QualityVerdict,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=[
                self.backend_task(),
                self.frontend_task(),
                self.test_task(),
                self.quality_task(),
            ],
            process=Process.hierarchical,
            manager_agent=self.engineering_lead(),
            tracing=True,
            verbose=True,
        )
