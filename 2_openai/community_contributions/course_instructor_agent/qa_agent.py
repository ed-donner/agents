from typing import Literal

from pydantic import BaseModel, Field

from agents import Agent


class QAAgentInstructions():
    def name(self):
        return "qa_agent"
    
    def instructions(self):
        return (
            "You are a QA agent. Your job is to review the lesson content and practice activities to ensure"
            "they are aligned with the learning objectives and are appropriate for the course level."
            "For each lesson:"
            "Review the lesson content and practice activities."
            "Ensure they are aligned with the learning objectives and are appropriate for the course level."
            "Ensure they are appropriate for the course level."
        )
    
    def handoff_description(self):
        return self.instructions()
    
    def model(self) -> Literal["gpt-4o-mini", "gpt-4o"]:
        return "gpt-4o-mini"
    
class QualityAssurance(BaseModel):
    is_satisfied: bool = Field(description="Whether the course is satisfied with the quality")
    reason: str = Field(description="The reason if the satisfied or not, if not it should mention the step that needs to be improved")
    
class QAAgent():
    def __init__(self):
        instructions = QAAgentInstructions()
        self.agent = Agent(
            name=instructions.name(),
            instructions=instructions.instructions(),
            model="gpt-4o-mini",
            handoff_description=instructions.handoff_description(),
            output_type=QualityAssurance,
        )
    
    
    def as_tool(self):
        instructions = QAAgentInstructions()
        return self.agent.as_tool(tool_name=instructions.name(), tool_description=instructions.handoff_description())