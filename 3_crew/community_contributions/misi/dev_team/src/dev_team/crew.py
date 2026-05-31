from graphlib import CycleError, TopologicalSorter
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent
from pydantic import BaseModel, Field


class ModuleDesign(BaseModel):
    file_name: str = Field(
        ...,
        description="Python module filename ending with .py, for example account_management.py.",
    )
    purpose: str = Field(
        ...,
        description="Short explanation of the module responsibility.",
    )
    classes: list[str] = Field(
        default_factory=list,
        description="Class names to implement in the module.",
    )
    functions: list[str] = Field(
        default_factory=list,
        description="Important function or method signatures to implement.",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Other backend module filenames this module depends on.",
    )
    interaction_contracts: list[str] = Field(
        default_factory=list,
        description="How this module uses or is used by other modules.",
    )


class ApplicationDesign(BaseModel):
    architecture_overview: str = Field(
        ...,
        description="High-level architecture summary for the whole application.",
    )
    shared_data_models: list[str] = Field(
        default_factory=list,
        description="Shared entities, DTOs, or persisted records used across modules.",
    )
    backend_modules: list[ModuleDesign] = Field(
        ...,
        description="The backend modules the engineering lead decided are needed.",
    )
    frontend_summary: str = Field(
        ...,
        description="How app.py should use the backend modules together.",
    )


@CrewBase
class EngineeringTeam():
    """EngineeringTeam crew"""

    agents_config = "config/agents.yaml"

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config["engineering_lead"],
            verbose=True,
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_engineer"],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=500,
            max_retry_limit=3,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["frontend_engineer"],
            verbose=True,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["test_engineer"],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=500,
            max_retry_limit=3,
        )

    def kickoff(self, inputs: dict) -> object:
        design = self._kickoff_design_crew(inputs)
        implementation_tasks = self._build_runtime_tasks(inputs, design)
        implementation_crew = Crew(
            agents=[
                self.backend_engineer(),
                self.frontend_engineer(),
                self.test_engineer(),
            ],
            tasks=implementation_tasks,
            process=Process.sequential,
            verbose=True,
        )
        runtime_inputs = {
            **inputs,
            "design_summary": self._design_summary(design),
        }
        return implementation_crew.kickoff(inputs=runtime_inputs)

    def _kickoff_design_crew(self, inputs: dict) -> ApplicationDesign:
        design_task = Task(
            name="design_task",
            description=(
                "Design the application architecture from the requirements.\n"
                "Decide the backend Python modules that should exist.\n"
                "The design must contain multiple backend modules, not a single module.\n"
                "The modules must collaborate cleanly so one module's outputs or persisted state "
                "can be used by other modules.\n"
                "The frontend will be a single app.py that integrates the backend modules.\n"
                "Keep the architecture simple and coherent.\n"
                "Requirements:\n{requirements}"
            ),
            expected_output=(
                "A structured application design containing the architecture overview, shared data models, "
                "the backend modules to implement, each module's classes/functions/dependencies, "
                "and how app.py should compose them."
            ),
            agent=self.engineering_lead(),
            output_pydantic=ApplicationDesign,
            output_file="output/system_design.json",
        )
        design_crew = Crew(
            agents=[self.engineering_lead()],
            tasks=[design_task],
            process=Process.sequential,
            verbose=True,
        )
        result = design_crew.kickoff(inputs=inputs)
        design = result.pydantic or design_task.output.pydantic
        return self._normalize_design(design)

    def _normalize_design(self, design: ApplicationDesign) -> ApplicationDesign:
        normalized_modules = []
        for module in design.backend_modules:
            file_name = self._normalize_file_name(module.file_name)
            dependencies = [
                dependency
                for dependency in (
                    self._normalize_file_name(dependency)
                    for dependency in module.dependencies
                )
                if dependency != file_name
            ]
            normalized_modules.append(
                ModuleDesign(
                    file_name=file_name,
                    purpose=module.purpose,
                    classes=module.classes,
                    functions=module.functions,
                    dependencies=dependencies,
                    interaction_contracts=module.interaction_contracts,
                )
            )

        deduped = {}
        for module in normalized_modules:
            deduped[module.file_name] = module

        if len(deduped) < 2:
            raise ValueError("The design must define multiple backend modules, not a single module.")

        return ApplicationDesign(
            architecture_overview=design.architecture_overview,
            shared_data_models=design.shared_data_models,
            backend_modules=list(deduped.values()),
            frontend_summary=design.frontend_summary,
        )

    def _build_runtime_tasks(self, inputs: dict, design: ApplicationDesign) -> list[Task]:
        module_task_map: dict[str, Task] = {}
        ordered_modules = self._order_modules(design.backend_modules)
        design_summary = self._design_summary(design)

        for module in ordered_modules:
            dependency_tasks = [
                module_task_map[dependency]
                for dependency in module.dependencies
                if dependency in module_task_map
            ]
            module_task_map[module.file_name] = Task(
                name=f"build_{Path(module.file_name).stem}",
                description=self._module_task_description(module, design_summary),
                expected_output=(
                    f"The full {module.file_name} module as raw Python code only. "
                    "Output only valid Python code without markdown or backticks."
                ),
                agent=self.backend_engineer(),
                context=dependency_tasks,
                output_file=f"output/{module.file_name}",
            )

        backend_tasks = [module_task_map[module.file_name] for module in ordered_modules]
        frontend_task = Task(
            name="build_frontend",
            description=self._frontend_task_description(design, ordered_modules),
            expected_output=(
                "The full app.py module as raw Python code only. "
                "It must import and use the generated backend modules together in one application. "
                "Output only valid Python code without markdown or backticks."
            ),
            agent=self.frontend_engineer(),
            context=backend_tasks,
            output_file="output/app.py",
        )

        test_tasks = []
        for module in ordered_modules:
            test_name = f"test_{Path(module.file_name).stem}.py"
            related_context = [module_task_map[module.file_name]]
            related_context.extend(
                module_task_map[dependency]
                for dependency in module.dependencies
                if dependency in module_task_map
            )
            test_tasks.append(
                Task(
                    name=f"build_{Path(test_name).stem}",
                    description=self._test_task_description(module, design_summary),
                    expected_output=(
                        f"The full {test_name} module as raw Python code only. "
                        "Output only valid Python code without markdown or backticks."
                    ),
                    agent=self.test_engineer(),
                    context=related_context,
                    output_file=f"output/{test_name}",
                )
            )

        return backend_tasks + [frontend_task] + test_tasks

    def _module_task_description(self, module: ModuleDesign, design_summary: str) -> str:
        return (
            f"Implement the backend module {module.file_name}.\n"
            f"Module purpose: {module.purpose}\n"
            f"Classes to implement: {self._bullet_lines(module.classes)}\n"
            f"Functions or methods to implement: {self._bullet_lines(module.functions)}\n"
            f"Dependencies on other modules: {self._bullet_lines(module.dependencies)}\n"
            f"Interaction contracts: {self._bullet_lines(module.interaction_contracts)}\n"
            "Honor the architecture below and make sure this module collaborates cleanly with its dependencies.\n"
            f"{design_summary}"
        )

    def _frontend_task_description(
        self,
        design: ApplicationDesign,
        modules: list[ModuleDesign],
    ) -> str:
        module_names = ", ".join(module.file_name for module in modules)
        return (
            "Implement app.py as the single frontend application for the system.\n"
            f"It must integrate these backend modules: {module_names}.\n"
            f"Frontend guidance: {design.frontend_summary}\n"
            "The UI should be simple, but it must demonstrate the backend modules working together end to end.\n"
            f"{self._design_summary(design)}"
        )

    def _test_task_description(self, module: ModuleDesign, design_summary: str) -> str:
        test_name = f"test_{Path(module.file_name).stem}.py"
        return (
            f"Implement {test_name} to unit test {module.file_name}.\n"
            f"Focus on the module responsibility: {module.purpose}\n"
            f"Cover the module classes: {self._bullet_lines(module.classes)}\n"
            f"Cover the important interfaces: {self._bullet_lines(module.functions)}\n"
            "If the module depends on other generated modules, test the collaboration boundaries with mocks or realistic fixtures as appropriate.\n"
            f"{design_summary}"
        )

    def _order_modules(self, modules: list[ModuleDesign]) -> list[ModuleDesign]:
        module_map = {module.file_name: module for module in modules}
        graph = {
            module.file_name: {
                dependency
                for dependency in module.dependencies
                if dependency in module_map
            }
            for module in modules
        }
        try:
            ordered_names = list(TopologicalSorter(graph).static_order())
        except CycleError as exc:
            raise ValueError(
                "The design produced cyclic module dependencies. The engineering lead must define an acyclic module graph."
            ) from exc
        return [module_map[name] for name in ordered_names]

    def _design_summary(self, design: ApplicationDesign) -> str:
        lines = [
            f"Architecture overview: {design.architecture_overview}",
            f"Shared data models: {self._bullet_lines(design.shared_data_models)}",
            "Backend modules:",
        ]
        for module in design.backend_modules:
            lines.append(
                f"- {module.file_name}: {module.purpose}. "
                f"Dependencies: {', '.join(module.dependencies) if module.dependencies else 'none'}."
            )
        lines.append(f"Frontend summary: {design.frontend_summary}")
        return "\n".join(lines)

    def _normalize_file_name(self, file_name: str) -> str:
        normalized = file_name.strip()
        if not normalized.endswith(".py"):
            normalized = f"{normalized}.py"
        return Path(normalized).name

    def _bullet_lines(self, items: list[str]) -> str:
        return ", ".join(items) if items else "none specified"
