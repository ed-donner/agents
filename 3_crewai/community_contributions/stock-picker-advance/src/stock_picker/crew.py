from typing import List

from crewai import Agent, Crew, Process, Task, LLM
from crewai.memory.short_term.short_term_memory import ShortTermMemory
from crewai.memory.long_term.long_term_memory import LongTermMemory
from crewai.memory.entity.entity_memory import EntityMemory
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    SerperDevTool,
    WebsiteSearchTool,
    ScrapeWebsiteTool,
    CodeInterpreterTool,
)

from .schemas import (
    CompanyBriefList,
    ScreenerMetricsList,
    ValuationViewList,
    RiskNewsItemList,
    FinalShortlist,
)


# Optional: create a single search+scrape toolkit used by multiple agents
search_tool = SerperDevTool()
web_rag = WebsiteSearchTool()
scraper = ScrapeWebsiteTool()
code_tool = CodeInterpreterTool()

# Default LLM configuration
default_llm = LLM(model="gpt-4o-mini")
function_llm = LLM(model="gpt-4o-mini")

# Memory/embeddings configuration
# Uses OpenAI embeddings by default; relies on `OPENAI_API_KEY` in environment.
EMBEDDER_CONFIG = {
    "provider": "openai",
    "config": {
        "model": "text-embedding-3-small",
    },
}


@CrewBase
class StockPickerCrew:
    """Industry‑driven stock‑picking crew"""

    # Tell CrewAI where your YAML lives
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # === Agents ===
    @agent
    def manager(self) -> Agent:
        return Agent(
            config=self.agents_config["manager"],  # type: ignore[index]
            verbose=True,
            llm=default_llm,
        )

    @agent
    def industry_mapper(self) -> Agent:
        return Agent(
            config=self.agents_config["industry_mapper"],  # type: ignore[index]
            verbose=True,
            tools=[search_tool, web_rag],
            llm=default_llm,
            function_calling_llm=function_llm,
        )

    @agent
    def company_discovery_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["company_discovery_agent"],  # type: ignore[index]
            verbose=True,
            tools=[search_tool, web_rag, scraper],
            llm=default_llm,
            function_calling_llm=function_llm,
        )

    @agent
    def fundamental_screener(self) -> Agent:
        return Agent(
            config=self.agents_config["fundamental_screener"],  # type: ignore[index]
            verbose=True,
            tools=[search_tool, web_rag, scraper, code_tool],
            llm=default_llm,
            function_calling_llm=function_llm,
        )

    @agent
    def valuation_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["valuation_analyst"],  # type: ignore[index]
            verbose=True,
            tools=[code_tool],
            llm=default_llm,
            function_calling_llm=function_llm,
        )

    @agent
    def news_risk_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["news_risk_analyst"],  # type: ignore[index]
            verbose=True,
            tools=[search_tool, web_rag, scraper],
            llm=default_llm,
            function_calling_llm=function_llm,
        )

    @agent
    def shortlist_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["shortlist_writer"],  # type: ignore[index]
            verbose=True,
            llm=default_llm,
        )

    # === Tasks ===
    @task
    def map_industry(self) -> Task:
        return Task(
            config=self.tasks_config["map_industry"],  # type: ignore[index]
        )

    @task
    def company_discovery(self) -> Task:
        return Task(
            config=self.tasks_config["company_discovery"],  # type: ignore[index]
            output_json=CompanyBriefList,
        )

    @task
    def screen_fundamentals(self) -> Task:
        return Task(
            config=self.tasks_config["screen_fundamentals"],  # type: ignore[index]
            output_json=ScreenerMetricsList,
        )

    @task
    def valuation_rank(self) -> Task:
        return Task(
            config=self.tasks_config["valuation_rank"],  # type: ignore[index]
            output_json=ValuationViewList,
        )

    @task
    def news_and_risks(self) -> Task:
        return Task(
            config=self.tasks_config["news_and_risks"],  # type: ignore[index]
            output_json=RiskNewsItemList,
        )

    @task
    def compile_shortlist(self) -> Task:
        return Task(
            config=self.tasks_config["compile_shortlist"],  # type: ignore[index]
            output_json=FinalShortlist,
        )

    # === Crew ===
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.industry_mapper(),
                self.company_discovery_agent(),
                self.fundamental_screener(),
                self.valuation_analyst(),
                self.news_risk_analyst(),
                self.shortlist_writer(),
            ],
            tasks=[
                self.map_industry(),
                self.company_discovery(),
                self.screen_fundamentals(),
                self.valuation_rank(),
                self.news_and_risks(),
                self.compile_shortlist(),
            ],
            process=Process.sequential,
            # manager_agent=self.manager(),  # kept for easy switch back to hierarchical
            verbose=True,
            planning=True,  # let CrewAI plan sub-steps per task
            # Enable CrewAI memory and provide explicit storage locations
            memory=True,
            embedder=EMBEDDER_CONFIG,
            short_term_memory=ShortTermMemory(
                crew=None,  # Crew will be set internally by CrewAI
                embedder_config=EMBEDDER_CONFIG,
            ),
            long_term_memory=LongTermMemory(),
            entity_memory=EntityMemory(
                crew=None,  # Crew will be set internally by CrewAI
                embedder_config=EMBEDDER_CONFIG,
            ),
        )
