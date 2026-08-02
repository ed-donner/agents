from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from safe_agile_team.models import DesignDocument


@CrewBase
class SafeAgileTeam():

    agents_config = 'config/agents.yaml'
    tasks_config  = 'config/tasks.yaml'


    @agent
    def business_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['business_analyst'],
            verbose=True,
        )

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],
            verbose=True,
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500,
            max_retry_limit=5
        )

    @agent
    def integration_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['integration_lead'],
            verbose=True,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500,
            max_retry_limit=5
        )


    def build_modules(self, output):

        design       = output.pydantic
        requirements = output.raw   # the BA's requirements flowed through via context

        print(f"\n>>> Engineering lead planned {len(design.modules)} modules\n")

        # loop: call backend engineer once per module
        module_code = {}
        for i, module in enumerate(design.modules):
            print(f"  [{i+1}/{len(design.modules)}] writing {module.filename}...")

            others = [m for m in design.modules if m.filename != module.filename]
            others_text = "\n".join(
                f"  - {m.filename}: {m.description[:200]}" for m in others
            ) or "  none"

            t = Task(
                config=self.tasks_config['backend_code_task'],
                agent=self.backend_engineer(),
            )

            result = Crew(
                agents=[self.backend_engineer()],
                tasks=[t],
                process=Process.sequential,
                verbose=True,
            ).kickoff(inputs={
                'module_filename':    module.filename,
                'module_name':        module.name,
                'module_description': module.description,
                'other_modules':      others_text,
                'requirements':       requirements,
            })

            module_code[module.filename] = result.raw

        print("\n>>> all modules written - running finishing team...\n")

        # --- integration lead ---
        modules_summary = "\n\n".join(
            f"=== {filename} ===\n{code[:800]}"
            for filename, code in module_code.items()
        )
        integration_task = Task(
            config=self.tasks_config['integration_task'],
            agent=self.integration_lead(),
        )
        Crew(
            agents=[self.integration_lead()],
            tasks=[integration_task],
            process=Process.sequential,
            verbose=True,
        ).kickoff(inputs={
            'modules_summary': modules_summary,
            'main_module':     design.main_module,
            'main_class':      design.main_class,
        })

        # frontend engineer
        main_module_code = module_code.get(design.main_module, '')
        frontend_task = Task(
            config=self.tasks_config['frontend_task'],
            agent=self.frontend_engineer(),
        )
        Crew(
            agents=[self.frontend_engineer()],
            tasks=[frontend_task],
            process=Process.sequential,
            verbose=True,
        ).kickoff(inputs={
            'main_module':        design.main_module,
            'main_module_no_ext': design.main_module.replace('.py', ''),
            'main_class':         design.main_class,
            'main_module_code':   main_module_code,
        })

        # test engineer
        test_task = Task(
            config=self.tasks_config['test_task'],
            agent=self.test_engineer(),
        )
        Crew(
            agents=[self.test_engineer()],
            tasks=[test_task],
            process=Process.sequential,
            verbose=True,
        ).kickoff(inputs={
            'main_module':      design.main_module,
            'main_class':       design.main_class,
            'main_module_code': main_module_code,
        })

        print("\n>>> all done!\n")


    @task
    def requirements_task(self) -> Task:
        return Task(
            config=self.tasks_config['requirements_task'],
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'],
            output_pydantic=DesignDocument,
            callback=self.build_modules,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )