from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent

from ghost_writer.models import Idea, Plot, Characters, Chapter, Act, Scene, Book, ArtisticVision
from ghost_writer.services.book_writer_service import BookWriterService
from ghost_writer.tools.transcribe_tool import TranscribeTool
from ghost_writer.tools.illustrator_tool import IllustratorTool
from ghost_writer.utils.filesystem_utils import purge_directory
from ghost_writer.utils.markdown_utils import add_page_break, header_markdown, image_markdown

from typing import List

@CrewBase
class GhostWriter():
    """GhostWriter crew"""

    agents: List[BaseAgent]
    tasks: List[Task]
    
    # A cost savings measure that is useful when testing and debugging
    disable_illustration: bool = False
    
    book_writer: BookWriterService = None

    @before_kickoff
    def on_before_kickoff(self, inputs):
        # Delete the output directory if it exists
        purge_directory('output')

        self.book_writer = BookWriterService(
            author_agent=self.author(),
            disable_illustration=self.disable_illustration)

        return inputs

    @agent
    def idea_developer(self) -> Agent:
        return Agent(
            config=self.agents_config['idea_developer'],
            verbose=True
        )

    @agent
    def plot_developer(self) -> Agent:
        return Agent(
            config=self.agents_config['plot_developer'], 
            verbose=True
        )
    
    @agent
    def character_developer(self) -> Agent:
        return Agent(
            config=self.agents_config['character_developer'],
            verbose=True
        )
    
    @agent
    def art_director(self) -> Agent:
        return Agent(
            config=self.agents_config['art_director'],
            verbose=True
        )
    
    @agent
    def outline_developer(self) -> Agent:
        return Agent(
            config=self.agents_config['outline_developer'],
            verbose=True
        )
    
    @agent
    def author(self) -> Agent:
        return Agent(
            config=self.agents_config['author'],
            verbose=True
        )

    @task
    def ideation_task(self) -> Task:
        return Task(
            config=self.tasks_config['ideation_task'],
            output_pydantic=Idea,
        )
    
    @task
    def plot_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['plot_development_task'],
            output_pydantic=Plot,
        )
    
    @task
    def character_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['character_development_task'],
            output_pydantic=Characters,
        )

    def on_act_created(self, task_output):
        act = task_output.pydantic
        self.book_writer.write_act(act)
        self.book_writer.save_pdf()

    def on_book_created(self, task_output):
        book = task_output.pydantic

        self.book_writer.write_book_cover(book)

    @task
    def book_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['book_development_task'],
            output_pydantic=Book,
            callback=self.on_book_created,
        )

    def on_artistic_vision_created(self, task_output):
        self.book_writer.set_artistic_vision(task_output.pydantic)


    @task
    def artistic_vision_task(self) -> Task:
        return Task(
            config=self.tasks_config['artistic_vision_task'],
            output_pydantic=ArtisticVision,
            callback=self.on_artistic_vision_created,
        )

    @task
    def act1_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['act1_development_task'],
            output_pydantic=Act,
            callback=self.on_act_created,
        )
    
    @task
    def act2_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['act2_development_task'],
            output_pydantic=Act,
            callback=self.on_act_created,
        )
    
    @task
    def act3_development_task(self) -> Task:
        return Task(
            config=self.tasks_config['act3_development_task'],
            output_pydantic=Act,
            callback=self.on_act_created,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
            memory=True
        )
