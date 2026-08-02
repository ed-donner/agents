from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, FileReadTool, DirectoryReadTool
from pydantic import BaseModel, Field
from .tools.system_tools import AdvancedFileWriterTool
from .tools.qa_tools import CodeExecutionTool
from typing import List, Optional
import os

# --- Structured Output Models ---
class AgentSchema(BaseModel):
    role: str
    goal: str
    backstory: str
    tools: List[str] = Field(default_factory=list)

class TaskSchema(BaseModel):
    name: str
    description: str
    expected_output: str
    assigned_agent_role: str

class ProjectBlueprint(BaseModel):
    project_name: str
    stack: str
    required_agents: List[AgentSchema]
    dynamic_tasks: List[TaskSchema]

@CrewBase
class DevSwarmCrew():
    """DevSwarm: The Self-Configuring Autonomous Agency"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    high_reasoning_model = os.getenv("MANAGER_MODEL", "gpt-4o")
    standard_model = os.getenv("MODEL", "gpt-4o-mini")

    def hire_dynamic_agent(self, schema: AgentSchema) -> Agent:
        """Instantiates a new specialist agent with mandatory file-writing tools."""
        writer_tool = AdvancedFileWriterTool()
        
        tool_map = {
            "FileWriterTool": writer_tool,
            "Advanced FileWriter": writer_tool,
            "FileReadTool": FileReadTool(),
            "SerperDevTool": SerperDevTool(),
            "DirectoryReadTool": DirectoryReadTool(directory_path='project_output/src'),
            "CodeExecutionTool": CodeExecutionTool()
        }
        
        # Combine tools from blueprint and always ensure writer is present
        assigned_tools = [tool_map[t] for t in schema.tools if t in tool_map]
        if writer_tool not in assigned_tools:
            assigned_tools.append(writer_tool)
        
        return Agent(
            role=schema.role,
            goal=schema.goal,
            backstory=schema.backstory,
            tools=assigned_tools,
            llm=self.standard_model,
            verbose=True,
            allow_delegation=False # Force them to work rather than talk to a manager
        )

    @agent
    def architect(self) -> Agent:
        return Agent(
            config=self.agents_config['architect'], 
            tools=[SerperDevTool(), AdvancedFileWriterTool()],
            llm=self.high_reasoning_model,
            verbose=True
        )

    @task
    def discovery_design_task(self) -> Task:
        return Task(
            config=self.tasks_config['discovery_design_task'],
            output_pydantic=ProjectBlueprint
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.architect()],
            tasks=[self.discovery_design_task()],
            process=Process.sequential,
            verbose=True
        )