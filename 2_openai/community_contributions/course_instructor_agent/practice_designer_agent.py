from typing import Literal

from pydantic import BaseModel, Field

from agents import Agent


class PracticeDesignerInstructions():
    def name(self):
        return "practice_designer"
    
    def instructions(self):
        return (
            "You are a test designer agent. Based on lesson content and learning objectives, you generate:"
            "Multiple choice questions (MCQs)"
            "Short-answer questions"
            "Case-based or scenario-driven exercises (if applicable)"
            "Include answers and explanations for each item."
            "Ensure difficulty aligns with the lesson level and purpose (formative or summative assessment)."
            "Ensure coverage of all critical concepts."
        )

    def handoff_description(self):
        return self.instructions()
    
    def model(self) -> Literal["gpt-4o-mini", "gpt-4o"]:
        return "gpt-4o-mini"

class Question(BaseModel):
    question: str = Field(description="The question to be asked from the student")
    answer: str = Field(description="The answer to the question")
    explanation: str = Field(description="The explanation of the answer")

class Practice(BaseModel):
    questions: list[Question]

class PracticeDesignerAgent():
    def __init__(self):
        instructions = PracticeDesignerInstructions()
        self.agent = Agent(
            name=instructions.name(),
            instructions=instructions.instructions(),
            model=instructions.model(),
            handoff_description=instructions.handoff_description(),
            output_type=Practice,
        )
        
    def as_tool(self):
        instructions = PracticeDesignerInstructions()
        return self.agent.as_tool(tool_name=instructions.name(), tool_description=instructions.handoff_description())
    