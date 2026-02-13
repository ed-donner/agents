"""Jira Support Crew: multi-agent support using Jira MCP-style tools. LLM: local Ollama or Gemini."""
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

from .tools.jira_tools import list_epics, list_boards, list_sprints, create_epic, create_sprint

# Disable tool result caching so Jira tools always run with current env (e.g. JIRA_PROJECT_KEY).
# Otherwise CrewAI reuses cached "404" when the agent passes project_key="PROJ".
_no_cache = lambda *args, **kwargs: False
for t in (list_epics, list_boards, list_sprints, create_epic, create_sprint):
    if hasattr(t, "cache_function"):
        t.cache_function = _no_cache


def _get_llm():
    """Use local Ollama by default; set USE_OLLAMA=false and GOOGLE_API_KEY for Gemini."""
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)

    use_ollama = os.getenv("USE_OLLAMA", "true").strip().lower() in ("true", "1", "yes")

    if use_ollama:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        # CrewAI talks to Ollama via OpenAI-compatible API (ollama exposes it)
        return LLM(
            model=f"ollama/{model}",
            base_url=base_url,
            api_key="ollama",  # not validated by Ollama
            temperature=0.2,
        )

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    if not api_key:
        return None
    return LLM(model="google/gemini-2.0-flash", api_key=api_key, temperature=0.2)


@CrewBase
class JiraSupportCrew:
    """Multi-agent crew for Jira support: specialist (tools), docs agent, synthesizer."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def jira_specialist(self) -> Agent:
        llm = _get_llm()
        return Agent(
            config=self.agents_config["jira_specialist"],
            tools=[list_epics, list_boards, list_sprints, create_epic, create_sprint],
            verbose=True,
            llm=llm,
        )

    @agent
    def docs_agent(self) -> Agent:
        llm = _get_llm()
        return Agent(
            config=self.agents_config["docs_agent"],
            verbose=True,
            llm=llm,
        )

    @agent
    def synthesizer(self) -> Agent:
        llm = _get_llm()
        return Agent(
            config=self.agents_config["synthesizer"],
            verbose=True,
            llm=llm,
        )

    @task
    def jira_task(self) -> Task:
        return Task(config=self.tasks_config["jira_task"])

    @task
    def docs_task(self) -> Task:
        return Task(config=self.tasks_config["docs_task"])

    @task
    def synthesize_task(self) -> Task:
        return Task(config=self.tasks_config["synthesize_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
