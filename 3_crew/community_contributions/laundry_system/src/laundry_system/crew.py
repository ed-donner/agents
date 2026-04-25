from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from pathlib import Path
from crewai import Task
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

# @CrewBase
# class LaundrySystem():
#     """LaundrySystem crew"""

#     agents: List[BaseAgent]
#     tasks: List[Task]

#     # Learn more about YAML configuration files here:
#     # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
#     # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
#     # If you would like to add tools to your agents, you can learn more about it here:
#     # https://docs.crewai.com/concepts/agents#agent-tools
#     @agent
#     def product_owner(self) -> Agent:
#         return Agent(
#             config=self.agents_config['product_owner'], # type: ignore[index]
#             verbose=True
#         )

#     @agent
#     def system_architect(self) -> Agent:
#         return Agent(
#             config=self.agents_config['system_architect'], # type: ignore[index]
#             verbose=True
#         )

#     @agent
#     def backend_engineer(self) -> Agent:
#         return Agent(
#             config=self.agents_config['backend_engineer'], # type: ignore[index]
#             verbose=True
#         )

#     @agent
#     def flutter_engineer(self) -> Agent:
#         return Agent(
#             config=self.agents_config['flutter_engineer'], # type: ignore[index]
#             verbose=True
#         )

#     @agent
#     def devops_engineer(self) -> Agent:
#         return Agent(
#             config=self.agents_config['devops_engineer'], # type: ignore[index]
#             verbose=True
#         )

#     @agent
#     def qa_reviewer(self) -> Agent:
#         return Agent(
#             config=self.agents_config['qa_reviewer'], # type: ignore[index]
#             verbose=True
#         )
#     # To learn more about structured task outputs,
#     # task dependencies, and task callbacks, check out the documentation:
#     # https://docs.crewai.com/concepts/tasks#overview-of-a-task
#     @task
#     def define_mvp(self) -> Task:
#         return Task(
#             config=self.tasks_config['define_mvp'], # type: ignore[index]
#         )

#     @task
#     def design_architecture(self) -> Task:
#         return Task(
#             config=self.tasks_config['design_architecture'], # type: ignore[index]
#         )

#     @task
#     def backend_api(self) -> Task:
#         return Task(
#             config=self.tasks_config['backend_api'], # type: ignore[index]
#         )

#     @task
#     def flutter_app(self) -> Task:
#         return Task(
#             config=self.tasks_config['flutter_app'], # type: ignore[index]
#         )

#     @task
#     def deployment(self) -> Task:
#         return Task(
#             config=self.tasks_config['deployment'], # type: ignore[index]
#         )

#     @task
#     def qa_review(self) -> Task:
#         return Task(
#             config=self.tasks_config['qa_review'], # type: ignore[index]
#             output_file='report.md'
#         )

#     @crew
#     def crew(self) -> Crew:
#         """Creates the LaundrySystem crew"""
#         # To learn how to add knowledge sources to your crew, check out the documentation:
#         # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

#         return Crew(
#             agents=self.agents, # Automatically created by the @agent decorator
#             tasks=self.tasks, # Automatically created by the @task decorator
#             process=Process.sequential,
#             verbose=True,
#             # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
#         )
    
  
@CrewBase
class LaundrySystemImplementation():
    """LaundrySystemImplementation crew"""

   
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def backend_builder(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_builder'],
            verbose=True
        )

    @agent
    def flutter_builder(self) -> Agent:
        return Agent(
            config=self.agents_config['flutter_builder'],
            verbose=True
        )

    @agent
    def devops_builder(self) -> Agent:
        return Agent(
            config=self.agents_config['devops_builder'],
            verbose=True
        )

    @agent
    def repo_integrator(self) -> Agent:
        return Agent(
            config=self.agents_config['repo_integrator'],
            verbose=True
        )

    
    @crew
    def crew(self) -> Crew:
        from pathlib import Path

        # Escape curly braces in file content to prevent template variable interpolation
        mvp = Path("output/mvp_scope.md").read_text().replace('{', '{{').replace('}', '}}')
        architecture = Path("output/system_architecture.md").read_text().replace('{', '{{').replace('}', '}}')
        api = Path("output/backend_api.md").read_text().replace('{', '{{').replace('}', '}}')
        devops = Path("output/devops.md").read_text().replace('{', '{{').replace('}', '}}')
        flutterapp = Path("output/flutter_app.md").read_text().replace('{', '{{').replace('}', '}}')


        implement_backend_task = Task(
            description=f"""
            You are implementing the backend system.

            MVP REQUIREMENTS:
            {mvp}

            SYSTEM ARCHITECTURE:
            {architecture}

            API SPECIFICATION:
            {api}

            Rules:
            - Generate REAL Node.js code
            - Use Express + PostgreSQL
            - Output folder paths explicitly
            - Do not explain, only output code
            """,
            expected_output=
                """A complete backend source tree with runnable code. Backend source code including:
                - API routes
                - Models
                - Database schema
                - Auth & payment integrations""",
            agent=self.backend_builder(),
            output_file="crew2_output/backend.md"
        )
      
        implement_flutter_task = Task(
            description=f"""
                Implement the Flutter Android app strictly following:

                MVP REQUIREMENTS:
                {mvp}

                SYSTEM ARCHITECTURE:
                {architecture}

                Project Structure:
                {flutterapp}

                API SPECIFICATION:
                {api}


                Rules:
                - Generate Flutter project with structure
                - Screens
                - State management
                - API integration
                - Output folder paths explicitly
                - Do not explain, only output code
                - Produce real Flutter code, not pseudocode.Use clean architecture and production conventions.
                """,
            expected_output=
                """Flutter project structure with:
                - Screens
                - State management
                - API integration""",
            agent=self.flutter_builder(),
            output_file="crew2_output/flutter.md"
        )

        implement_devops_task = Task(
            description=f"""
                Implement deployment artifacts based on:

                SYSTEM ARCHITECTURE:
                {architecture}

                Deployment Strategy:
                {devops}

                Rules:
                - Include Dockerfiles, CI/CD pipelines, and environment setup.
                - Output folder paths explicitly
                - Do not explain, only output code
                - Produce real Flutter code, not pseudocode.Use clean architecture and production conventions.
                """,
            expected_output=
                """Deployment-ready configuration including Docker and CI/CD.""",
            agent=self.devops_builder(),
            output_file="crew2_output/devops.md"
        )


        integration_review_task = Task(
            description=f"""
                Review all subsystems for naming consistency, env vars,
                ports, and integration correctness.
                """,
            expected_output=
                """Integration review notes with recommendations for consistency,
                environment variables, port configurations, and system integration points.""",
            agent=self.repo_integrator(),
            output_file="crew2_output/integration_notes.md"
        )


        return Crew(
            agents=self.agents,
            tasks= [implement_backend_task, implement_flutter_task, implement_devops_task, integration_review_task],
            process=Process.sequential,
            verbose=True
        )