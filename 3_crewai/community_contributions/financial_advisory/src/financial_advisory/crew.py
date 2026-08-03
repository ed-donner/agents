from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class FinancialAdvisory:
    """FinancialAdvisory crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def user_data_summarizer(self) -> Agent:
        return Agent(
            config=self.agents_config["user_data_summarizer"],
            verbose=True,
        )

    @agent
    def emergency_fund_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config["emergency_fund_advisor"],
            verbose=True,
        )

    @agent
    def investment_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_advisor"],
            verbose=True,
        )

    @agent
    def insurance_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config["insurance_advisor"],
            verbose=True,
        )

    @agent
    def reporting_analyst_financial_plan(self) -> Agent:
        return Agent(
            config=self.agents_config["reporting_analyst_financial_plan"],
            verbose=True,
        )

    @task
    def summarize_data_task(self) -> Task:
        return Task(config=self.tasks_config["summarize_data_task"])

    @task
    def emergency_fund_task(self) -> Task:
        return Task(config=self.tasks_config["emergency_fund_task"])

    @task
    def investment_task(self) -> Task:
        return Task(config=self.tasks_config["investment_task"])

    @task
    def insurance_task(self) -> Task:
        return Task(config=self.tasks_config["insurance_task"])

    @task
    def financial_plan_report_task(self) -> Task:
        return Task(config=self.tasks_config["financial_plan_report_task"])

    @crew
    def financial_advisory_crew(self) -> Crew:
        return Crew(
            name="Financial Advisory Crew",
            agents=self.agents,
            tasks=self.tasks,
            processes=Process.sequential,
            verbose=True,
        )
