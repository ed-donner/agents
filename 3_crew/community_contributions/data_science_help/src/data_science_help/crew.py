import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from data_science_help.tools.tools import (
    get_web_search_tool,
    get_code_interpreter_tool,
    get_json_search_tool,
    get_file_read_tool,
)

from data_science_help.structured_outputs import (
    DatasetAudit, CleaningPlan, CleanedDataRef, VisualSummary,
    StepAudit
)


serper_api_key = os.getenv("SERPER_API_KEY")


@CrewBase
class DataScienceTeam():
    """DataScienceTeam Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'


    @agent
    def design_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['design_agent'],
            verbose=True,
        )


    @agent
    def analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst_agent'],
            verbose=True,
            tools=[get_code_interpreter_tool()]
        ) 


    @agent
    def clean_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['clean_agent'],
            verbose=True,
            #allow_code_execution=True,
            #code_execution_mode="safe",
            tools=[get_code_interpreter_tool(), get_json_search_tool(), get_file_read_tool()]
        )


    @agent
    def visualization_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['visualization_agent'],
            verbose=True,
            #allow_code_execution=True,
            #code_execution_mode="safe",
            tools=[get_code_interpreter_tool(), get_file_read_tool()],
        )


    @agent
    def frontend_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["frontend_agent"],
            verbose=True,
            tools=[get_code_interpreter_tool(), get_file_read_tool()],
        )
        

    @agent
    def tester_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["tester_agent"],
            verbose=True,
            #allow_code_execution=True,
            #code_execution_mode="safe", 
            tools=[get_json_search_tool(), get_file_read_tool()],
        )
    
    @agent
    def controller_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['controller_agent'],
            verbose=True,
            tools=[get_json_search_tool(), get_file_read_tool()]
        )


    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'],
        )

    @task
    def analyze_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_task'],
        )
   

    @task
    def clean_and_apply_task(self) -> Task:
        return Task(
            config=self.tasks_config['clean_and_apply_task'],
        )

    @task
    def visualize_task(self) -> Task:
        return Task(
            config=self.tasks_config['visualize_task'],
        )


    @task
    def frontend_task(self) -> Task:
        return Task(config=self.tasks_config["frontend_task"])

    @task
    def ui_smoke_test_task(self) -> Task:
        return Task(config=self.tasks_config["ui_smoke_test_task"])

    @task
    def control_task(self) -> Task:
        return Task(
            config=self.tasks_config['control_task'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates Data Science Crew"""
        return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        verbose=True,
    )