from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from event_research.tools.firebase import get_db


class EventToolInput(BaseModel):
    """Input schema for DatabaseToolInput."""
    name: str = Field(..., description="Name of the event.")
    startDate: str = Field(..., description="Start date of the event.")
    endDate: str = Field(..., description="End date of the event.")
    shortDescription: str = Field(..., description="Short description of the event.")
    description: str = Field(..., description="Description of the event.")

class EventsToolInput(BaseModel):
    events: list[EventToolInput] = Field(..., description="List of events to store")


class DatabaseTool(BaseTool):
    name: str = "Firebase Database Tool"
    description: str = (
        "This tool is used to interEventToolInputbase database. It is used to input events data into the database."
    )
    args_schema: Type[BaseModel] = EventsToolInput

    def _run(self, events:list[EventToolInput]) -> str:
        db = get_db()
        for event in events:
            print(event)
            db.collection("event_prospects").add(event)
        return "Done adding events to the database. Event added: " + str(len(events))
