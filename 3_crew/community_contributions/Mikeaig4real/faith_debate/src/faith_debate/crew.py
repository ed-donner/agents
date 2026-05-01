from crewai import Agent
from crewai.project import CrewBase, agent

@CrewBase
class FaithDebate():
    """FaithDebate crew definitions"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def moderator(self) -> Agent:
        return Agent(
            config=self.agents_config['moderator'],
            verbose=True
        )

    @agent
    def christian_debater(self) -> Agent:
        return Agent(
            config=self.agents_config['christian_debater'],
            verbose=True
        )

    @agent
    def muslim_debater(self) -> Agent:
        return Agent(
            config=self.agents_config['muslim_debater'],
            verbose=True
        )

    @agent
    def atheist_debater(self) -> Agent:
        return Agent(
            config=self.agents_config['atheist_debater'],
            verbose=True
        )

    @agent
    def agnostic_debater(self) -> Agent:
        return Agent(
            config=self.agents_config['agnostic_debater'],
            verbose=True
        )
