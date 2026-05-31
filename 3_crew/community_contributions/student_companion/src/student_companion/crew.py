from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import SerperDevTool
import re

def clean_markdown_output(text: str) -> str:
    """Remove markdown code fences if present."""
    print("Cleaning markdown output...")
    return re.sub(r"^```[\w]*\n|```$", "", text.strip(), flags=re.MULTILINE).strip()

@CrewBase
class StudentCompanion():
    """StudentCompanion crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def intent_recognizer(self) -> Agent:
        return Agent(config=self.agents_config['intent_recognizer'], # type: ignore[index]
            verbose=True
        )

    @agent
    def topic_generator(self) -> Agent:
        return Agent(config=self.agents_config['topic_generator'], # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def study_content_generator(self) -> Agent:
        return Agent(config=self.agents_config['study_content_generator'], 
            verbose=True, 
            tools=[SerperDevTool()]
        )

    @agent
    def question_generator(self) -> Agent:
        return Agent(config=self.agents_config['question_generator'], 
            verbose=True, 
            tools=[SerperDevTool()]
        )

    @agent
    def output_parser(self) -> Agent:
        return Agent(config=self.agents_config['output_parser'], 
            verbose=True
        )
    
    @task
    def intent_recognizing_task(self) -> Task:
        return Task(config=self.tasks_config['intent_recognizing_task'], 
                    output_file='outputs/0_intent_recognizing_task_report.md')
    
    @task
    def topic_generation_task(self) -> Task:
        return Task(config=self.tasks_config['topic_generation_task'], 
                    output_file='outputs/1_topic_generation_task_report.md')

    @task
    def study_content_generation_task(self) -> Task:
        return Task(config=self.tasks_config['study_content_generation_task'],
                    output_file='outputs/2_study_content_generation_task_report.md')
        
    @task
    def question_generator_task(self) -> Task:
        return Task(config=self.tasks_config['question_generator_task'], 
                    output_file='outputs/3_question_generator_task_report.md')

    @task
    def output_parser_task(self) -> Task:
        def post_process(output: str) -> str:
            return clean_markdown_output(output)
        
        return Task(config=self.tasks_config['output_parser_task'], 
                    output_file='outputs/4_formatted_report.md',
                    postprocess=post_process)

    @crew
    def crew(self) -> Crew:
        """Creates the StudentCompanion crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge


        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True
        )
