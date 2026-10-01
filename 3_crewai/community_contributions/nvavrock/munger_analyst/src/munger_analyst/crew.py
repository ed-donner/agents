from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool


def _knowledge_sources() -> list[TextFileKnowledgeSource]:
    """Load Munger + promoted personal models from the project knowledge/ folder."""
    # crew.py lives at src/munger_analyst/crew.py → parents[2] is project root
    knowledge_dir = Path(__file__).resolve().parents[2] / "knowledge"
    paths = [
        knowledge_dir / "charlie_mungers_mental_models.md",
        knowledge_dir / "my_mental_models.md",
    ]
    existing = [p for p in paths if p.exists()]
    if not existing:
        return []
    # Pass Path objects (not str) so CrewAI does not prefix knowledge/ again.
    return [TextFileKnowledgeSource(file_paths=existing)]


@CrewBase
class MungerAnalyst:
    """MungerAnalyst crew — research + Munger-style equity memo."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],  # type: ignore[index]
            verbose=True,
            tools=[SerperDevTool()],
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["analyst"],  # type: ignore[index]
            knowledge_sources=_knowledge_sources(),
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],  # type: ignore[index]
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["analysis_task"],  # type: ignore[index]
            # Path comes from inputs["memo_path"] via YAML: output/YYYYMMDD_<slug>_memo.md
        )

    @crew
    def crew(self) -> Crew:
        """Creates the MungerAnalyst crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            chat_llm="openai/gpt-4o-mini",
            tracing=True,
        )
