from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv

load_dotenv(override=True)

@CrewBase
class Interview():
    """Interview crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def candidate_agent(self) -> Agent:
        return Agent(config=self.agents_config['candidate_agent'], verbose=True)

    @agent
    def interviewer_agent(self) -> Agent:
        return Agent(config=self.agents_config['interviewer_agent'], verbose=True)

    @task
    def generate_question_task(self) -> Task:
        return Task(config=self.tasks_config['generate_question_task'])

    @task
    def answer_question_task(self) -> Task:
        return Task(config=self.tasks_config['answer_question_task'])

    @task
    def hire_task(self) -> Task:
        return Task(config=self.tasks_config['hire_task'])

    @crew
    def crew(self) -> Crew:
        """Creates the Interview crew (full flow for backward compatibility)"""
        return Crew(
            agents=self.agents, 
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )

    def crew_phase1_questions(self) -> Crew:
        """Phase 1: Generate the same questions for all candidates."""
        return Crew(
            agents=[self.interviewer_agent()],
            tasks=[self.generate_question_task()],
            process=Process.sequential,
            verbose=True
        )

    def crew_phase2_answer(self) -> Crew:
        """Phase 2: Candidate answers the shared questions."""
        return Crew(
            agents=[self.candidate_agent()],
            tasks=[self.answer_question_task()],
            process=Process.sequential,
            verbose=True
        )

    def crew_phase3_hire(self) -> Crew:
        """Phase 3: Compare all candidates and make hiring decision."""
        return Crew(
            agents=[self.interviewer_agent()],
            tasks=[self.hire_task()],
            process=Process.sequential,
            verbose=True
        )
