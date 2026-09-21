"""Week 3 capstone (CrewAI) - a research crew the idiomatic way.

Config-as-data: the agents and tasks live in config/agents.yaml + config/tasks.yaml, and this
@CrewBase class wires them with the @agent / @task / @crew decorators. The framework auto-collects
the decorated methods into self.agents and self.tasks. Run via main.py.
"""
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class ResearchCrew:
    """Researcher -> Writer, run sequentially, with the research handed to the writer as context."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config["researcher"], verbose=True)

    @agent
    def writer(self) -> Agent:
        return Agent(config=self.agents_config["writer"], verbose=True)

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def write_task(self) -> Task:
        # write_task lists research_task as `context` in tasks.yaml, so the writer receives its output
        return Task(config=self.tasks_config["write_task"], output_file="briefing.md")

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)
