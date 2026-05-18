from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are an event researcher tasked with writing json data for events in a given period and location"
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should come up with a final json data for events in a given period and location, this data will then be put into a database"
)

class EventData(BaseModel):
    name: str = Field(description="The name of the event")
    date: str = Field(description="The date of the event")
    location: str = Field(description="The location of the event")
    description: str = Field(description="The description of the event")
    url: str = Field(description="The url of the event")



writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=EventData,
)