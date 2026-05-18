from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

@CrewBase
class StartupIdeaBrainstormer():
    """StartupIdeaBrainstormer crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def researcher(self) -> Agent:
        return Agent( config=self.agents_config['researcher'],  verbose=True )

    @agent
    def critic(self) -> Agent:
        return Agent( config=self.agents_config['critic'],  verbose=True )

    @agent
    def product_strategist(self) -> Agent:
        return Agent( config=self.agents_config['product_strategist'],  verbose=True )

    @agent
    def synthesizer(self) -> Agent:
        return Agent( config=self.agents_config['synthesizer'],  verbose=True )


    @task
    def research_task(self) -> Task:
        return Task( config=self.tasks_config['research_task'])

    @task
    def critical_evaluation_task(self) -> Task:
        return Task(config=self.tasks_config['critical_evaluation_task'])
   
    @task
    def product_strategy_task(self) -> Task:
        return Task(config=self.tasks_config['product_strategy_task'])

    @task
    def validation_report_task(self) -> Task:
        return Task(config=self.tasks_config['validation_report_task'])


    @crew
    def crew(self) -> Crew:
        """Creates the StartupIdeaBrainstormer crew"""

        print(self.agents, "agents_config")
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)
