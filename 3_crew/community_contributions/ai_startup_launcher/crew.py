from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew
try:
    from crewai_tools import SerperDevTool
    search_tool = SerperDevTool()
except Exception:
    search_tool = None

from tools.investor_finder_tool import InvestorFinderTool
from tools.email_sender_tool import EmailSenderTool
from tools.reply_tracker_tool import ReplyTrackerTool


@CrewBase
class AIStartupLauncher:
    """AI Startup Launcher Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # Market research agent
    @agent
    def market_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["market_researcher"],
            tools=[search_tool] if search_tool else [],
            verbose=True,
            memory=True
        )

    # Idea validator
    @agent
    def idea_validator(self) -> Agent:
        return Agent(
            config=self.agents_config["idea_validator"],
            tools=[search_tool] if search_tool else [],
            verbose=True
        )

    # MVP builder
    @agent
    def mvp_builder(self) -> Agent:
        return Agent(
            config=self.agents_config["mvp_builder"],
            allow_code_execution=False,  # Disable code execution for security
            verbose=True
        )

    # Investor finder
    @agent
    def investor_finder(self) -> Agent:
        return Agent(
            config=self.agents_config["investor_finder"],
            tools=[InvestorFinderTool()],
            verbose=True
        )

    # Outreach agent
    @agent
    def outreach_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["outreach_agent"],
            tools=[EmailSenderTool(), ReplyTrackerTool()],
            verbose=True
        )

    # Tasks
    @task
    def discover_idea(self) -> Task:
        return Task(
            config=self.tasks_config["discover_idea"]
        )

    @task
    def validate_idea(self) -> Task:
        return Task(
            config=self.tasks_config["validate_idea"]
        )

    @task
    def build_mvp(self) -> Task:
        return Task(
            config=self.tasks_config["build_mvp"]
        )

    @task
    def find_investors(self) -> Task:
        return Task(
            config=self.tasks_config["find_investors"]
        )

    @task
    def send_outreach(self) -> Task:
        return Task(
            config=self.tasks_config["send_outreach"]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            tracing=True
        )