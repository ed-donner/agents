from agents import Agent, ModelSettings

from models.models import Clarification


INSTRUCTIONS = """
You are clarifying agent. You need to ask 3 clarification questions based on input query.  
You will use answeres of those questions to build follow up research context.
Only ask three questions.
"""


clarification_agent = Agent(   
    name = "Clarification Agent",
    instructions= INSTRUCTIONS,
    model = "gpt-4o-mini",
    output_type=Clarification,
)