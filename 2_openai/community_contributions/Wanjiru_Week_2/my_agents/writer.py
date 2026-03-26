from agents import Agent
from pydantic import BaseModel

class Report(BaseModel):
    content: str

writer = Agent(
    name="Writer",
    instructions="""
    Write a detailed research report (1000+ words).
    Use markdown formatting.
    """,
    model="gpt-4o-mini",
    output_type=Report,
)
