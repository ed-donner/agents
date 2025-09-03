from typing import Literal

from curriculum_designer_agent import Curriculum, CurriculumDesignerAgent
from instruction_designer_agent import Instruction, InstructionDesignerAgent
from practice_designer_agent import Practice, PracticeDesignerAgent
from pydantic import BaseModel
from qa_agent import QAAgent, QualityAssurance

from agents import Agent

INSTRUCTIONS = (
    """You are an coordinator agent, you are responsible for coordinating the course instruction flow.
    1. First the curriculum designer agent will design the curriculum.
    2. Then the instruction designer must design the course instruction.
    3. Then the practice designer must design the practice exercises.
    4. Then the QA agent must assure that this course has the right quality. 
    If it doesn't have the right quality, you should start the flow again from the step the qa agent wasn't satisfied with.
    """
)

class CoordinatorInstructions():
    def name(self):
        return "coordinator"
    
    def instructions(self):
        return (
            "You are an coordinator agent, you are responsible for coordinating the course instruction flow."
            "1. First the curriculum designer agent will design the curriculum."
            "2. Then the instruction designer must design the course instruction."
            "3. Then the practice designer must design the practice exercises."
            "4. Then the QA agent must assure that this course has the right quality." 
                "If it doesn't have the right quality, you should start the flow again from the step the qa agent wasn't satisfied with."
            "5. In the end based on all of the information provided to you in above steps, write a clear and concise course plan."
        )
        
    def handoff_description(self):
        return self.instructions()
    
    def model(self) -> Literal["gpt-4o-mini", "gpt-4o"]:
        return "gpt-4o-mini"
    

class Course(BaseModel):
    curriculum: Curriculum
    instruction: Instruction
    practice: Practice
    qa: QualityAssurance


class CoordinatorAgent():
    def __init__(self):
        self.curriculum_designer_agent = CurriculumDesignerAgent()
        self.instruction_designer_agent = InstructionDesignerAgent()
        self.practice_designer_agent = PracticeDesignerAgent()
        self.qa_agent = QAAgent()
        self.agent = self.init_agent()

    def get_agent(self):
        return self.agent

    def init_agent(self):
        tools = [
            self.curriculum_designer_agent.as_tool(),
            self.instruction_designer_agent.as_tool(),
            self.practice_designer_agent.as_tool(),
            self.qa_agent.as_tool(),
        ]
        instructions = CoordinatorInstructions()
        agent = Agent(
            name=instructions.name(),
            instructions=instructions.instructions(),
            model=instructions.model(),
            tools=tools,
        )
        return agent

    def as_tool(self):
        instructions = CoordinatorInstructions()
        return self.agent.as_tool(tool_name=instructions.name(), tool_description=instructions.handoff_description())
