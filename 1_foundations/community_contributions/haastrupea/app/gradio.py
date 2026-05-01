# import pipiline class to runb the show for

from os import name
import  gradio as gr
from src.pipeline import Pipeline


class DigitalAsistant:
    examples: list[str] = [
    "Can you walk me through your experience and the kind of systems you’ve built?",
    "What are your core strengths as a software engineer and what problems do you specialize in?",
    "Can you explain a complex project you’ve worked on and the impact it had?",
    "How can I get in touch with you or discuss a potential opportunity?"
]
    def __init__(self) -> None:
        self.pipeline = Pipeline()
        self.name: str = Pipeline.config.get('name')

    def welcome_greeting (self):
    
        greeting = f"""
            I build systems that work under real-world pressure. \n\n
            Hi, my name is {self.name}, I'm a Software Engineer with almost a decade of experience.\n\n
            Feel free to ask me about my experience, projects, or how I design systems.
            You can use the suggested questions below to get started.
        """

        return greeting
        
    
    def run(self):
        
        greeting = self.welcome_greeting()
        with gr.Blocks() as ui:

            gr.Markdown(f"""
            # Chat with {self.name} \n\n\n

            {greeting}

            """)
            gr.ChatInterface(
                self.pipeline.chat,
                textbox= gr.Textbox(placeholder="Ask me something..."),
                examples= self.examples,
                type="messages"
            )

        ui.launch(share=False, server_name= "0.0.0.0")