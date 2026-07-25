from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput
from crewai_tools import SerperDevTool
from typing import List
from health_aid.schema import HealthMetrics, RiskReport, DietPlan


# --- Condition ---
def needs_intervention(output: TaskOutput) -> bool:
    """Run the Nutritionist task only if risks are moderate or critical."""
    report: RiskReport = output.pydantic
    return report.requires_intervention if report else False


# --- Callbacks ---
def on_metrics_parsed(output: TaskOutput):
    metrics: HealthMetrics = output.pydantic
    print(f"Flagged metrics: {metrics.flagged}")

def on_risks_found(output: TaskOutput):
    report: RiskReport = output.pydantic
    print(f"Severity: {report.severity}")
    if report.severity == "critical":
        print("Alert: Critical health risks detected!")

def on_diet_plan_created(output: TaskOutput):
    plan: DietPlan = output.pydantic
    print(f"Diet plan created: {plan.recommendations}")

def on_report_written(output: TaskOutput):
    with open("report.md", "w") as f:
        f.write(output.raw)
    print("Wellness report saved to report.md")


@CrewBase
class HealthAid():
    """HealthAid crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # --- Agents ---
    @agent
    def triage_nurse(self) -> Agent:
        return Agent(config=self.agents_config['triage_nurse'], verbose=True)

    @agent
    def medical_researcher(self) -> Agent:
        return Agent(config=self.agents_config['medical_researcher'], tools=[SerperDevTool()], verbose=True)

    @agent
    def nutritionist(self) -> Agent:
        return Agent(config=self.agents_config['nutritionist'], verbose=True)

    @agent
    def report_writer(self) -> Agent:
        return Agent(config=self.agents_config['report_writer'], verbose=True)

    # --- Tasks ---
    @task
    def triage_nurse_task(self) -> Task:
        return Task(
            config=self.tasks_config['triage_nurse_task'],
            output_pydantic=HealthMetrics,
            callback=on_metrics_parsed
        )

    @task
    def medical_researcher_task(self) -> Task:
        return Task(
            config=self.tasks_config['medical_researcher_task'],
            output_pydantic=RiskReport,
            callback=on_risks_found
        )

    @task
    def nutritionist_task(self) -> ConditionalTask:
        return ConditionalTask(
            config=self.tasks_config['nutritionist_task'],
            output_pydantic=DietPlan,
            condition=needs_intervention,
            callback=on_diet_plan_created
        )

    @task
    def report_writer_task(self) -> Task:
        return Task(
            config=self.tasks_config['report_writer_task'],
            output_file='report.md',
            callback=on_report_written
        )

    # --- Crew ---
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )