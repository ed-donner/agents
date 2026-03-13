from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# Define Ollama LLMs
llm_debater1 = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
llm_debater2 = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
llm_judge = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class HousepurchaseDebate():
    """HousepurchaseDebate crew"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def debater1(self) -> Agent:
        return Agent(
            config=self.agents_config['debater1'], 
            llm=llm_debater1,
            verbose=True)

    @agent
    def debater2(self) -> Agent:
        return Agent(
            config=self.agents_config['debater2'], 
            llm=llm_debater2,
            verbose=True)

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config['judge'], # type: ignore[index]
            llm=llm_judge,
            verbose=True
        )

    @task
    def propose(self) -> Task:
        return Task(
            config=self.tasks_config['propose'], # type: ignore[index]
            output_file='report.md'
        )

    @task
    def oppose(self) -> Task:
        return Task(
            config=self.tasks_config['oppose'], # type: ignore[index]
            output_file='report.md'
        )

    @task
    def decide(self) -> Task:
        return Task(
            config=self.tasks_config['decide'], # type: ignore[index]
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the House Purchase Debate crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )