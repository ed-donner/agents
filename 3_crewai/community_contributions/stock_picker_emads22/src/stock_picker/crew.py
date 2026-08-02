import os
from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from .tools.push_tool import PushNotificationTool


class TrendingCompany(BaseModel):
    """A company that is in the news and attracting attention"""

    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    reason: str = Field(description="Reason this company is trending in the news")


class TrendingCompanyList(BaseModel):
    """List of multiple trending companies that are in the news"""

    companies: List[TrendingCompany] = Field(
        description="List of companies trending in the news"
    )


class TrendingCompanyResearch(BaseModel):
    """Detailed research on a company"""

    name: str = Field(description="Company name")
    market_position: str = Field(
        description="Current market position and competitive analysis"
    )
    future_outlook: str = Field(description="Future outlook and growth prospects")
    investment_potential: str = Field(
        description="Investment potential and suitability for investment"
    )


class TrendingCompanyResearchList(BaseModel):
    """A list of detailed research on all the companies"""

    research_list: List[TrendingCompanyResearch] = Field(
        description="Comprehensive research on all trending companies"
    )


@CrewBase
class StockPicker:
    """Defines the StockPicker crew with its agents, tasks, and execution flow."""

    @agent
    def trending_company_finder(self) -> Agent:
        # Agent responsible for finding trending companies using a search tool
        return Agent(
            config=self.agents_config["trending_company_finder"],
            tools=[SerperDevTool()],
            memory=True,
        )

    @agent
    def financial_researcher(self) -> Agent:
        # Agent responsible for researching the companies found in the first step
        return Agent(
            config=self.agents_config["financial_researcher"], tools=[SerperDevTool()]
        )

    @agent
    def stock_picker(self) -> Agent:
        # Agent responsible for analyzing research data and selecting the best company
        return Agent(
            config=self.agents_config["stock_picker"],
            tools=[PushNotificationTool()],
            memory=True,
        )

    @task
    def find_trending_companies(self) -> Task:
        # Task executed by trending_company_finder to get trending companies
        return Task(
            config=self.tasks_config["find_trending_companies"],
            output_pydantic=TrendingCompanyList,
        )

    @task
    def research_trending_companies(self) -> Task:
        # Task executed by financial_researcher to analyze each trending company
        return Task(
            config=self.tasks_config["research_trending_companies"],
            output_pydantic=TrendingCompanyResearchList,
        )

    @task
    def pick_best_company(self) -> Task:
        # Task executed by stock_picker to decide on the best company for investment
        return Task(config=self.tasks_config["pick_best_company"])

    @crew
    def crew(self) -> Crew:
        """
        Defines and returns the Crew configuration for this project.
        This setup uses CrewAI's built-in memory system and OpenAI embeddings
        with Chroma as the storage backend.
        """

        # Ensure Chroma has access to the OpenAI API key.
        # Chroma uses the variable CHROMA_OPENAI_API_KEY internally instead of OPENAI_API_KEY.
        # If OPENAI_API_KEY exists but CHROMA_OPENAI_API_KEY does not,
        # we copy the value over so Chroma can initialize embeddings properly.
        if "OPENAI_API_KEY" in os.environ and "CHROMA_OPENAI_API_KEY" not in os.environ:
            os.environ["CHROMA_OPENAI_API_KEY"] = os.environ["OPENAI_API_KEY"]

        # (Optional) Define where CrewAI should store its memory databases locally.
        # This includes:
        #   - Short-term memory (Chroma)
        #   - Long-term memory (SQLite)
        #   - Entity memory (Chroma)
        #
        # By default, CrewAI stores data in an OS-specific directory, for example:
        #   Windows: C:\Users\<user>\AppData\Local\CrewAI\stock_picker
        #
        # Setting this environment variable forces CrewAI to store memory
        # inside the project folder instead, making it easier to inspect and version-control.
        #
        # NOTE:
        # If we pass a *relative path* (e.g. "./memory"), CrewAI will append it to its
        # default base directory under AppData. Using `os.path.abspath()` converts the path
        # to an absolute one, ensuring the memory directory is created exactly inside the
        # project folder, not in AppData.
        os.environ["CREWAI_STORAGE_DIR"] = os.path.abspath("./memory")

        # Create the manager agent.
        # This agent will coordinate the execution of tasks when using hierarchical processing.
        # The 'allow_delegation=True' flag allows it to delegate tasks to other agents.
        manager = Agent(
            config=self.agents_config["manager"],
            allow_delegation=True,
        )

        # Return the Crew instance.
        # - agents: the list of agents participating in the workflow
        # - tasks: all defined tasks to execute
        # - process: hierarchical mode, with the manager agent orchestrating the flow
        # - verbose: True to print logs during execution
        # - manager_agent: the coordinating agent
        # - memory=True: enables short-term, long-term, and entity memory automatically
        # - embedder: specifies the embedding provider and model for memory operations
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            memory=True,
            embedder={
                "provider": "openai",
                "config": {
                    # The small OpenAI embedding model is cost-efficient and fast.
                    "model": "text-embedding-3-small"
                },
            },
        )
