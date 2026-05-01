from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class SoftwareEngineeringCrew():
	"""SoftwareEngineeringCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def engineering_lead(self) -> Agent:
		return Agent(config=self.agents_config['engineering_lead'], verbose=True)

	@agent
	def backend_engineer(self) -> Agent:
		return Agent(config=self.agents_config['backend_engineer'], verbose=True)

	@agent
	def test_engineer(self) -> Agent:
		return Agent(config=self.agents_config['test_engineer'], verbose=True)

	@agent
	def frontend_engineer(self) -> Agent:
		return Agent(config=self.agents_config['frontend_engineer'], verbose=True)

	@task
	def design_task(self) -> Task:
		return Task(config=self.tasks_config['design_task'], output_file='output/design.md')

	@task
	def implementation_task(self) -> Task:
		return Task(config=self.tasks_config['implementation_task'], output_file='output/backend.py')

	@task
	def testing_task(self) -> Task:
		return Task(config=self.tasks_config['testing_task'], output_file='output/test_backend.py')

	@task
	def frontend_task(self) -> Task:
		return Task(config=self.tasks_config['frontend_task'], output_file='output/app.py')

	@crew
	def crew(self) -> Crew:
		"""Creates the SoftwareEngineeringCrew crew"""
		return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=True,
		)
