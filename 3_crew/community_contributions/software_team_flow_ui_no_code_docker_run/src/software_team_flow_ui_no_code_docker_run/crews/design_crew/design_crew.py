from tabnanny import verbose
from typing import List
from crewai_tools import SerperDevTool
from crewai import Agent, Crew, Process, Task, LLM
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


# Configure Ollama LLM as OpenAI-compatible
ollama = LLM(
    model="llama3.2",
    base_url="http://localhost:11434/v1", 
    api_key="none", 
    temperature=0.2
)


@CrewBase
class DesignCrew:
    """Poem Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    
    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config["engineering_lead"],  
            tools=[SerperDevTool()],
            llm=ollama,
        )

    @agent
    def business_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["business_engineer"],  
            tools=[SerperDevTool()]
        )

    @task
    def design_app(self) -> Task:
        return Task(
            config=self.tasks_config["design_app"],  
        )
        
    @task
    def create_class_diagram(self) -> Task:
        return Task(
            config=self.tasks_config["create_class_diagram"],  
        )

    @task
    def create_sequence_diagram(self) -> Task:
        return Task(
            config=self.tasks_config["create_sequence_diagram"],  
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Design Crew"""

        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
        )
