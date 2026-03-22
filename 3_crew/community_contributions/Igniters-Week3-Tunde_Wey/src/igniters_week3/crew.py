from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class LessonPlanCrew:
    """Lesson plan pipeline: research → author → pedagogy critic. Gemini only, no web tools."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def curriculum_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["curriculum_researcher"],
            verbose=True,
        )

    @agent
    def lesson_author(self) -> Agent:
        return Agent(
            config=self.agents_config["lesson_author"],
            verbose=True,
        )

    @agent
    def pedagogy_critic(self) -> Agent:
        return Agent(
            config=self.agents_config["pedagogy_critic"],
            verbose=True,
        )

    @task
    def research_lesson_topic(self) -> Task:
        return Task(
            config=self.tasks_config["research_lesson_topic"],
        )

    @task
    def write_lesson_plan(self) -> Task:
        return Task(
            config=self.tasks_config["write_lesson_plan"],
        )

    @task
    def critique_and_finalize(self) -> Task:
        return Task(
            config=self.tasks_config["critique_and_finalize"],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
