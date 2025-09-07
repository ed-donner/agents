from tabnanny import verbose
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import FileReadTool, FileWriterTool, DirectoryReadTool

@CrewBase
class ProjectTeam():
    """ProjectTeam crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'], # type: ignore[index]
            verbose=True,
            tools=[FileWriterTool(), FileReadTool()]
        )

    @agent
    def python_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['python_engineer'],
            verbose=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500, 
            max_retry_limit=3,
            tools=[FileWriterTool(), FileReadTool(), DirectoryReadTool()]
       )
    
    @agent
    def ui_designer(self) -> Agent:
        return Agent(
            config=self.agents_config['ui_designer'], # type: ignore[index]
            verbose=True,
            tools=[FileWriterTool(), FileReadTool()]
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            verbose=True,
            code_execution_mode="safe",  # Uses Docker for safety
            max_execution_time=500, 
            max_retry_limit=3,
            tools=[FileWriterTool(), FileReadTool()]
        )

    @task
    def system_design_task(self) -> Task:
        return Task(
            config=self.tasks_config['system_design_task'],
            verbose=True,
        )

    @task
    def development_task(self) -> Task:
        return Task(
            config=self.tasks_config['development_task'],
            verbose=True,
            tools=[FileWriterTool()]
        )
        
    @task
    def ui_design_task(self) -> Task:
        return Task(
            config=self.tasks_config['ui_design_task'],
            verbose=True,
        )

    @task
    def frontend_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_development_task'],
            verbose=True,
            tools=[FileWriterTool()]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ProjectTeam crew"""

        # project_manager = Agent(
        #     role="Project Manager",
        #     goal="Efficiently manage the crew and ensure high-quality task completion",
        #     backstory="""
        #     You're an experienced project manager, skilled in overseeing complex projects and guiding teams to success.

        #     Assign system design document task to Engineering Lead.
        #     Assign module development task to Python Engineer.
        #         - Provide only module name defined  
            
        #     Do not analyze requriements.
        #     Do not craft system design.
        #     Do not develop module by yourself.
        #     """,
        #     verbose=True,
        #     allow_delegation=True,
        #     llm="openai/gpt-4o"
        # )

        project_manager = Agent(
            role="Project Manager",
            goal="Efficiently manage the crew and ensure high-quality task completion",
            backstory="""
            You're an experienced project manager, skilled in overseeing complex projects and guiding teams to success.

            System Design Assigement:
            Assign system design task to Engineering Lead ONLY ONE time. 
            This ONE system design will be used by Python Engineer whenever the engineer implement a module.

            Module Implement Assigement:
            You review the system design created by Engieering Lead and break it down to modules.
            You assign each module to Python Engineer with the module detail in the system document written by Engineering Lead.
            When you assing a module, make sure not assigning a module that already assigned to Python Engineer before.
            Module implementation is considered as completed when all modules degined in the system design are implemented by Python Engineer.
            
            Do not analyze requriements by yourself.
            Do not craft system design by yourself.
            Do not develop module by yourself.   
            """, # type: ignore[index]
            verbose=True,
            allow_delegation=True,
            llm="openai/gpt-4o"
        )

        return Crew(
            #agents=[],
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.hierarchical,
            #manager_agent=project_manager,
            manager_llm="openai/gpt-4o-mini",
            planning=True,
            verbose=True

            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
