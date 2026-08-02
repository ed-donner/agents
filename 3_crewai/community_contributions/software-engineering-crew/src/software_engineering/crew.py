import json
from crewai import Agent, Crew, Process, Task, TaskOutput
from crewai.project import CrewBase, agent, crew, task
from software_engineering.schema import ProjectSpec


@CrewBase
class EngineeringTeam():
    """Dynamic EngineeringTeam crew with callback-based task chaining."""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],
            verbose=True
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=1000,
            max_retry_limit=3
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=500,
            max_retry_limit=3
        )

    def handle_design_output(self, output: TaskOutput):
        """Executed automatically after design_task completes."""
        print("\n✅ [Callback] Design task completed. Parsing plan and building tasks...\n")

        try:
            # Parse output from the design phase
            spec_data = json.loads(output.raw)
            spec = ProjectSpec(**spec_data)
        except Exception as e:
            print(f"❌ Failed to parse design output: {e}")
            return

        # Dynamically build backend, test, and frontend tasks
        dynamic_tasks = self.build_dynamic_tasks(json.dumps(spec_data))

        # Create and run the secondary crew dynamically
        dynamic_crew = Crew(
            agents=[
                self.backend_engineer(),
                self.test_engineer(),
                self.frontend_engineer(),
            ],
            tasks=dynamic_tasks,
            process=Process.sequential,
            verbose=True,
        )

        print("\n🚀 [Callback] Kicking off dynamically generated tasks...\n")
        dynamic_crew.kickoff()

    @task
    def design_task(self) -> Task:
        """Initial design task (triggers dynamic build on completion)."""
        return Task(
            config=self.tasks_config['design_task'],
            agent=self.engineering_lead(),
            output_file="output/project_plan.json",
            callback=self.handle_design_output
        )

    def build_dynamic_tasks(self, design_output: str):
        """Build tasks dynamically based on engineering lead's plan."""
        spec = ProjectSpec(**json.loads(design_output))

        print(f"Spec: {spec}")
        print(f"Design output: {design_output}")
        print(f"Spec data: {json.loads(design_output)}")

        tasks = []
        for module in spec.modules:
            print(f"Building tasks for module: {module.name}")
            print(f"Class name: {module.class_name}")
            print(f"Module name: {module.name}")
            print(f"Purpose: {module.purpose}")

            # Backend task
            tasks.append(Task(
                description=f"Implement module {module.name} with class {module.class_name}. Purpose: {module.purpose}",
                expected_output="A valid Python file implementing the described class and purpose.",
                agent=self.backend_engineer(),
                output_file=f"output/backend/{module.name}",
                inputs={
                    "module_name": module.name,
                    "class_name": module.class_name,
                    "purpose": module.purpose
                }
            ))

            # Test task
            tasks.append(Task(
                description=f"Write unit tests for the module {module.name}.",
                expected_output=f"A pytest-compatible test file test_{module.name}.",
                agent=self.test_engineer(),
                output_file=f"output/tests/test_{module.name}",
                inputs={
                    "module_name": module.name,
                    "class_name": module.class_name,
                    "purpose": module.purpose
                }
            ))

        # Frontend task (only one per project)
        tasks.append(Task(
            description="Write a Gradio app (app.py) that demonstrates the backend modules.",
            expected_output="A Python Gradio UI in app.py that imports the generated backend classes.",
            agent=self.frontend_engineer(),
            output_file="output/app.py",
            inputs={
                "modules": [m.model_dump() for m in spec.modules]
            }
        ))

        return tasks

    @crew
    def crew(self) -> Crew:
        """Creates the crew with just the design task initially"""
        return Crew(
            agents=[self.engineering_lead()],
            tasks=[self.design_task()],
            process=Process.sequential,
            verbose=True,
        )
