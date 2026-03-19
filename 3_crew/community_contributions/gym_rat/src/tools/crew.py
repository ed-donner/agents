from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class FitnessCrew():
    """simple fitness planning crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # --- agents ---

    @agent
    def fitness_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['fitness_agent'],
            verbose=True
        )

    @agent
    def planner_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['planner_agent'],
            verbose=True
        )

    @task
    def generate_workout_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_workout_task'],
        )

    @task
    def generate_meal_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_meal_task'],
        )

    # @task
    # def adjust_plan_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['adjust_plan_task'],
    #     )

    @crew
    def crew(self) -> Crew:
        """builds the crew (sequential for now, might change later)"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )