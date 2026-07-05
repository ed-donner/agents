from crewai import Agent, Crew, Process, Task
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.project import CrewBase, agent, crew, task

from crewai_framework_helper.rag import project_root
from crewai_framework_helper.tools.framework_search import FrameworkSearchTool


def _knowledge_sources() -> list[TextFileKnowledgeSource]:
    tips = project_root() / "knowledge" / "usage_tips.txt"
    if not tips.is_file():
        return []
    return [TextFileKnowledgeSource(file_paths=[tips])]


@CrewBase
class FrameworkHelperCrew:
    """Answer CrewAI framework questions using RAG over upstream source and docs."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def framework_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["framework_researcher"],
            verbose=True,
            tools=[FrameworkSearchTool()],
        )

    @agent
    def framework_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config["framework_advisor"],
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def answer_task(self) -> Task:
        return Task(config=self.tasks_config["answer_task"])

    @crew
    def crew(self) -> Crew:
        sources = _knowledge_sources()
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            knowledge_sources=sources if sources else None,
        )
