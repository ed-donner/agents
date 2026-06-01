from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
import os
from dotenv import load_dotenv


@CrewBase
class Interview():
    """Interview crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    llm = LLM(
    model="groq/openai/gpt-oss-20b",
    temperature=0.7
)

    @agent
    def interviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['interviewer'], # type: ignore[index]
            verbose=True,
            llm=self.llm
        )

    @agent
    def candidate(self) -> Agent:
        return Agent(
            config=self.agents_config['candidate'], # type: ignore[index]
            verbose=True,
            llm=self.llm
        )

    @agent
    def recruiter(self) -> Agent:
        return Agent(
            config=self.agents_config['recruiter'], # type: ignore[index]
            verbose=True,
            llm=self.llm
        )


    @task
    def ask_question(self) -> Task:
        return Task(
            config=self.tasks_config['ask_question'], # type: ignore[index]
            llm=self.llm
        )

    @task
    def give_answer(self) -> Task:
        return Task(
            config=self.tasks_config['give_answer'], # type: ignore[index]
            llm=self.llm
        )

    @task
    def evaluate_candidate(self) -> Task:
        return Task(
            config=self.tasks_config['evaluate_candidate'], # type: ignore[index]
            llm=self.llm,
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the InterviewP1 crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
