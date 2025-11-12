from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from .tools.dom_raw_extract_tool import DomExtractRawTool
from typing import List
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class TddQaEngineeringTeam():
    """TddQaEngineeringTeam crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    # @agent
    # def dom_scan_agent(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['dom_scan_agent'], # type: ignore[index]
    #         tools=[DomExtractRawTool()],
    #         verbose=True
    #     )
    
    # @agent
    # def test_case_designer(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['test_case_designer'], # type: ignore[index]
    #         verbose=True
    #     )    
    
    @agent
    def automation_test_script_designer(self) -> Agent:
        return Agent(
            config=self.agents_config['automation_test_script_designer'], # type: ignore[index]
            verbose=True
        )  

    @agent
    def script_writer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['script_writer_agent'], # type: ignore[index]
            temperature=0.0,
            verbose=True
        )          

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    # @task
    # def dom_scan_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['dom_scan_task'], # type: ignore[index]
    #     )

    # @task
    # def test_case_designer_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['test_case_designer_task'], # type: ignore[index]
    #     )
    
    @task
    def automation_test_script_task(self) -> Task:
        return Task(
            config=self.tasks_config['automation_test_script_task'], # type: ignore[index]
            allow_code_execution=True,
            code_execution_mode="safe", 
            max_retry_limit=5,
        )

    @task
    def script_writer_task(self) -> Task:
        return Task(
            config=self.tasks_config['script_writer_task'], # type: ignore[index]
            allow_code_execution=True,
            code_execution_mode="safe", 
            max_retry_limit=5,            
        )        

    @crew
    def crew(self) -> Crew:
        """Creates the TddQaEngineeringTeam crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
