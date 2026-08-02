from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, FileWriterTool, SerperDevTool

# Import our custom tool
from code_phoenix.tools.notification_tool import PushNotificationTool

# For Structured Output
from pydantic import BaseModel, Field

class FixReport(BaseModel):
    summary: str = Field(..., description="Summary of what was fixed")
    verification_status: str = Field(..., description="Did the code run successfully? (Success/Fail)")
    fixed_file_path: str = Field(..., description="Path to the fixed file")

@CrewBase
class CodePhoenix():
    """CodePhoenix crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def investigator(self) -> Agent:
        return Agent(
            config=self.agents_config['investigator'],
            # We add SerperDevTool. If no key is found, it will try to skip/mock or fail gracefully depending on version.
            tools=[FileReadTool(), SerperDevTool()], 
            verbose=True
        )

    @agent
    def engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['engineer'],
            tools=[FileWriterTool(), FileReadTool()],
            allow_code_execution=True,  # Enable Code Execution
            
            # ⚠️ IMPORTANT: 
            # Use "safe" if you have Docker Desktop running
            # Use "unsafe" to run directly on your laptop (Easier for quick testing)
            code_execution_mode="safe", 
            verbose=True
        )

    @agent
    def manager(self) -> Agent:
        return Agent(
            config=self.agents_config['manager'],
            tools=[PushNotificationTool()],
            verbose=True
        )

    @task
    def investigate_task(self) -> Task:
        return Task(
            config=self.tasks_config['investigate_task'],
        )

    @task
    def fix_and_verify_task(self) -> Task:
        return Task(
            config=self.tasks_config['fix_and_verify_task'],
        )

    @task
    def notify_task(self) -> Task:
        return Task(
            config=self.tasks_config['notify_task'],
            output_pydantic=FixReport
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )