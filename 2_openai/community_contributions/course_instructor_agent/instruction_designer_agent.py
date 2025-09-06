from typing import Literal

from pydantic import BaseModel, Field

from agents import Agent


class InstructionDesignerInstructions():
    def name(self):
        return "instruction_designer"
    
    def instructions(self):
        return (
            "You are an instructional designer agent. Your job is to turn curriculum outlines into engaging,"
            "clear, and pedagogically sound lesson content."
            "For each lesson:"
            "Follow the learning objectives."
            "Write explanations, examples, and step-by-step breakdowns."
            "Incorporate analogies or visuals when appropriate (text description only)."
            "Keep tone aligned with the course level (beginner, intermediate, expert)."
            "Do not generate quizzes or assessments. Pass structured lessons to the next agent."
        )
    
    def handoff_description(self):
        return self.instructions()
    
    def model(self) -> Literal["gpt-4o-mini", "gpt-4o"]:
        return "gpt-4o-mini"
    
class Instruction(BaseModel):
    title: str = Field(description="The title of the instruction")
    description: str = Field(description="The description of the instruction")

class InstructionDesignerAgent():
    def __init__(self):
        instructions = InstructionDesignerInstructions()
        self.agent = Agent(
            name=instructions.name(),
            instructions=instructions.instructions(),
            model=instructions.model(),
            handoff_description=instructions.handoff_description(),
            output_type=Instruction,
        )
    
    def as_tool(self):
        instructions = InstructionDesignerInstructions()
        return self.agent.as_tool(tool_name=instructions.name(), tool_description=instructions.handoff_description())
