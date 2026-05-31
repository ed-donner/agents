from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are given a research query and optionally a conversation history of previous clarifying questions and answers." 
    "If asked to clarify, generate the next single clarifying question  that is specific, open-ended, and helps narrow the scope of the research. " 
    "If asked to refine, synthesize a refined query from the conversation."

)



class ClarifyingOutput(BaseModel):
    question: str| None = Field(default=None,description="The next adaptive question to ask the user") # the next adaptive question
    reason: str | None = Field(default=None,description="The reason for asking the clarifying question") 
    refined_query: str| None = Field(default=None,description="The final,refined query based on the answers given by the user")  


clarifying_agent = Agent(
    name="ClarifyingAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarifyingOutput,
)