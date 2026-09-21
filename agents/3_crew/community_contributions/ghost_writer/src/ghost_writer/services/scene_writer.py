from ghost_writer.models import Scene, Act, Chapter
from ghost_writer.tools.transcribe_tool import TranscribeTool
from ghost_writer.services.writer_templates import get_scene_task_prompt
from ghost_writer.utils.markdown_utils import header_markdown

from crewai import Agent

class SceneWriter:
    def __init__(self, author_agent: Agent, transcriber: TranscribeTool = None):
        self.transcriber = transcriber or TranscribeTool()
        self.author_agent = author_agent
    
    def write_scene(self, scene: Scene, act: Act, chapter: Chapter):
        scene_header = header_markdown(text=scene.scene_title, level=4)
        self.transcriber.run(content=scene_header)

        from crewai import Task
        task_description = get_scene_task_prompt(
            scene=scene,
            act=act,
            chapter=chapter
        )
        
        task = Task(
            description=task_description.strip(),
            expected_output="A well-written scene in markdown format.",
            agent=self.author_agent
        )
        paragraphs = task.execute_sync().raw
        self.transcriber.run(content=f"{paragraphs}\n\n")