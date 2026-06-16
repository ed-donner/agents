from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import os


@CrewBase
class DebateEngine():
    """DebateEngine crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"


#AGENTS
   
    @agent
    def prosecutor(self) -> Agent:
        cfg = self.agents_config["prosecutor"]
        return Agent(
            config=cfg,
            llm=os.getenv("DEBATE_PROSECUTOR_MODEL") or cfg.get("llm"),
        )

    @agent
    def defense(self) -> Agent:
        cfg = self.agents_config["defense"]
        return Agent(
            config=cfg,
            llm=os.getenv("DEBATE_DEFENSE_MODEL") or cfg.get("llm"),
        )

    @agent
    def evidence_analyst(self) -> Agent:
        cfg = self.agents_config["evidence_analyst"]
        return Agent(
            config=cfg,
            llm=os.getenv("DEBATE_EVIDENCE_ANALYST_MODEL") or cfg.get("llm"),
        )

    @agent
    def judge(self) -> Agent:
        cfg = self.agents_config["judge"]
        return Agent(
            config=cfg,
            llm=os.getenv("DEBATE_JUDGE_MODEL") or cfg.get("llm"),
        )

    @agent
    def fact_checker(self) -> Agent:
        cfg = self.agents_config["fact_checker"]
        return Agent(
            config=cfg,
            llm=os.getenv("DEBATE_FACT_CHECKER_MODEL") or cfg.get("llm"),
        )

#TASKS
 
    @task
    def extract_evidence(self) -> Task:
        return Task(
            config=self.tasks_config["extract_evidence"],
        )

    @task
    def prosecutor_opening(self) -> Task:
        return Task(
            config=self.tasks_config["prosecutor_opening"],
            context=[self.extract_evidence()],
        )

    @task
    def defense_opening(self) -> Task:
        return Task(
            config=self.tasks_config["defense_opening"],
            context=[self.extract_evidence(), self.prosecutor_opening()],
        )

    @task
    def prosecutor_rebuttal(self) -> Task:
        return Task(
            config=self.tasks_config["prosecutor_rebuttal"],
            context=[self.extract_evidence(), self.prosecutor_opening(), self.defense_opening()],
        )

    @task
    def defense_rebuttal(self) -> Task:
        return Task(
            config=self.tasks_config["defense_rebuttal"],
            context=[self.extract_evidence(), self.defense_opening(), self.prosecutor_rebuttal()],
        )

    @task
    def fact_check(self) -> Task:
        return Task(
            config=self.tasks_config["fact_check"],
            context=[
                self.extract_evidence(),
                self.prosecutor_opening(),
                self.defense_opening(),
                self.prosecutor_rebuttal(),
                self.defense_rebuttal(),
            ],
        )

    @task
    def closing_arguments(self) -> Task:
        return Task(
            config=self.tasks_config["closing_arguments"],
            context=[self.extract_evidence(), self.prosecutor_opening(), self.defense_opening()],
        )

    @task
    def final_verdict(self) -> Task:
        return Task(
            config=self.tasks_config["final_verdict"],
            context=[
                self.extract_evidence(),
                self.prosecutor_opening(),
                self.defense_opening(),
                self.prosecutor_rebuttal(),
                self.defense_rebuttal(),
                self.fact_check(),
                self.closing_arguments(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the DebateEngine crew"""
        
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
