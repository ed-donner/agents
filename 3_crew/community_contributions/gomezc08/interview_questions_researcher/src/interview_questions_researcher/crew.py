from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool
from typing import List

@CrewBase
class InterviewQuestionsResearcher():
    """InterviewQuestionsResearcher crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'], verbose=True, tools=[SerperDevTool()])

    @agent
    def recruiter(self) -> Agent:
        return Agent(config=self.agents_config['recruiter'], verbose=True)

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])

    @task
    def generate_interview_questions_task(self) -> Task:
        return Task(config=self.tasks_config['generate_interview_questions_task'], output_file='output/interview_questions.md')

    @crew
    def crew(self) -> Crew:
        """Creates the InterviewQuestionsResearcher crew"""

        return Crew(
            agents=self.agents, 
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
