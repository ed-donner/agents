from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from .tools.dom_extract_tool import DomExtractTool

@CrewBase
class QaTestingTeam():
    """QaTestingTeam crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def requirement_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['requirement_analyst'], # type: ignore[index]
            verbose=True
        )

    @agent
    def dom_scan_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['dom_scan_agent'], # type: ignore[index]
            tools=[DomExtractTool()],
            verbose=True
        ) 

    @agent
    def test_case_designer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_case_designer'], # type: ignore[index]
            verbose=True
        ) 
        
    @agent
    def automation_test_script_designer(self) -> Agent:
        return Agent(
            config=self.agents_config['automation_test_script_designer'], # type: ignore[index]
            allow_code_execution=True,
            code_execution_mode="safe", 
            max_execution_time=500, 
            max_retry_limit=5,
            verbose=True
        )   
              

    @task
    def analyze_requirements(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_requirements'], # type: ignore[index]
        )

    @task
    def dom_scan_task(self) -> Task:
        return Task(
            config=self.tasks_config['dom_scan_task']# type: ignore[index]
        )  

    @task
    def test_case_designer_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_case_designer_task']# type: ignore[index]
        )

    @task
    def automation_test_script_task(self) -> Task:
        return Task(
            config=self.tasks_config['automation_test_script_task']# type: ignore[index]
        )        

    @crew
    def crew(self) -> Crew:
        """Creates the QaTestingTeam crew"""
        
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
