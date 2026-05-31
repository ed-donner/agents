from crewai import Agent, Task, TaskOutput
from crewai.project import CrewBase, agent, task
from typing import Tuple, Any

@CrewBase
class Guardrails():
    def __init__(self, design_task_ref):
        self.design_task_ref = design_task_ref

    @agent
    def design_validation_lead(self) -> Agent:
        return Agent(
            role="QA Design Lead",
            goal="Audit the design documents for structural integrity and technical depth.",
            backstory="""You are a pedantic Lead Architect. You do not accept lazy work. 
            You check if 'todo.md' is comprehensive (5+ points) and if 'technical_spec.json' 
            is actually a valid JSON structure that maps all requirements.""",
            llm="gpt-4o", 
            verbose=True
        )

    @task
    def design_validation_task(self) -> Task:
        return Task(
            description="""Review the documents produced in the design phase. 
            1. Does todo.md have at least 5 bullet points in 'Development Phases'?
            2. Does technical_spec.json define clear methods for all requirements?
            If these criteria are not met, provide a detailed list of what to fix.""",
            expected_output="A report ending in either 'STATUS: PASS' or 'STATUS: FAIL' with fix instructions.",
            agent=self.design_validation_lead(),
            context=[self.design_task_ref] 
        )

    @staticmethod
    def validate_design_structure(result: TaskOutput) -> Tuple[bool, Any]:
        """Hard check for bullet points and sections"""
        content = result.raw
        if "Development Phases" not in content:
            return (False, "Missing 'Development Phases' section in todo.md.")
        if content.count("*") < 5:
            return (False, "The 'Development Phases' section needs at least 5 bullet points.")
        return (True, content)