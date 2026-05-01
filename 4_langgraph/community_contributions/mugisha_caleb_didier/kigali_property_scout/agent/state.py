"""Data models and state definitions"""

from typing import Annotated, List, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    stage: str
    budget: Optional[str]
    property_type: Optional[str]
    purpose: Optional[str]
    area: Optional[str]
    opportunities: Optional[list]


class IntakeExtraction(BaseModel):
    response: str = Field(description="The conversational reply to show the user")
    budget: Optional[str] = Field(default=None, description="Extracted budget if mentioned (e.g. '$50,000-$100,000', '30M RWF')")
    property_type: Optional[str] = Field(default=None, description="Extracted property type if mentioned (apartment, villa, house, commercial, land)")
    purpose: Optional[str] = Field(default=None, description="Extracted purpose if mentioned (own use, rental income, resale)")
    area: Optional[str] = Field(default=None, description="Extracted area of Kigali if mentioned (e.g. Nyarutarama, Kicukiro, Kimihurura)")
    all_gathered: bool = Field(default=False, description="True only when all 4 preferences (budget, property_type, purpose, area) are confirmed")


class Opportunity(BaseModel):
    developer_name: str = Field(default="", description="Real estate developer or agency name")
    project_name: str = Field(default="", description="Name of the project or listing")
    location: str = Field(default="", description="Specific location within Kigali")
    property_types: str = Field(default="", description="Types available (e.g. 2BR apartment, studio, 3BR villa)")
    price_range: str = Field(default="", description="Price range if explicitly found. Leave empty string if not confirmed in search results.")
    payment_plan: str = Field(default="", description="Payment terms if available (e.g. off-plan, 30% deposit). Leave empty string if unknown.")
    highlights: List[str] = Field(default_factory=list, description="Up to 3 key selling points from the source")
    source_link: str = Field(default="", description="URL source where this information was found")


class OpportunityList(BaseModel):
    opportunities: List[Opportunity] = Field(default_factory=list, description="Up to 4 real estate opportunities matching the user's preferences")
