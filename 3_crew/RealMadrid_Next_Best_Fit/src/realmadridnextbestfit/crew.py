from typing import List

from pydantic import BaseModel, Field

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool
from crewai.memory import Memory


class TrendingPlayer(BaseModel):
    name : str = Field(description="Name of the football player")
    current_club : str =  Field(description="Name of the club the player plays for")
    
class ScoutingOutput(BaseModel):
    listOfPlayers : List[TrendingPlayer] = Field(description='list of 5 chosen players')

class PlayersStats(BaseModel):
    name : str =  Field(description='name of the player')
    age : int = Field(description='age of the player')
    height : float = Field(description='height of the player in cms')
    matches_played : int = Field(description='total matches player by the player')
    goals : int = Field(description='total goals scored by the player')
    fitness_status : int = Field(description="Current injury status or physical fitness note.")
    estimated_wage : str = Field(description='Estimated weekly or yearly wage.')

class chosenPlayer(BaseModel):
    name: str = Field(description='name of the player')
    reason : str = Field(description= 'Reason for selecting this player amoung 4 others')
    key_attruibutes : PlayersStats = Field(description='Players attributes')

@CrewBase
class Realmadridnextbestfit():
    """Realmadridnextbestfit crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'


    @agent
    def trending_player_finder(self) -> Agent:
        return Agent(config=self.agents_config['trending_player_finder'], tools=[SerperDevTool()], verbose=True,
                    memory=True)
    
    @agent
    def research_analyst(self) -> Agent:
        return Agent(config=self.agents_config['research_analyst'], tools=[SerperDevTool()], verbose=True)
    
    @agent
    def coach(self) -> Agent:
        return Agent(config=self.agents_config['coach'], verbose=True, memory=True )


    @task
    def trending_player_task(self) -> Task:
        return Task(config=self.tasks_config['trending_player_task'],
                    verbose=True,
                    output_pydantic=ScoutingOutput)
    
    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'],
                    verbose=True,
                    output_pydantic=PlayersStats)
    
    @task
    def coach_task(self) -> Task:
        return Task(config=self.tasks_config['coach_task'],
                    verbose=True,
                    output_pydantic=chosenPlayer)


    @crew
    def crew(self) -> Crew:
        """Creates the Realmadridnextbestfit crew"""
       
        manager = Agent(config=self.agents_config['manager'],
                       verbose=True,
                       allow_delegation=True)

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            
            # Enables the unified short, long, and entity memory systems automatically
            memory=True, 
            
            # Customizes the global storage f`older directory (Replaces path="./memory/")
            storage_handler=None, # Leave None to let CrewAI handle DB structures internally
            
            # This configures your 'text-embedding-3-small' model globally for all memory types
            embedder={
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small"
                }
            }
        )
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        
