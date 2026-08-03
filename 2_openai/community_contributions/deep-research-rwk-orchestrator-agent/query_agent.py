"""
Query agent receives, avaluates, questions the user's prompts
until the conversation produces a clear, concise, and specific query
"""

from pydantic import BaseModel, Field
from agents import Agent

import parameters as param


# structure of output
class Query(BaseModel):
    query: str = Field(description="The query received from the user")
    is_clear: bool = Field(description="Whether the query is clear enough to be answered.")
    question: str = Field(description="A question about the query.")
    

# make sure the model spec is current
query_agent = Agent[Query](
    name="QueryAgent",
    instructions= param.INSTRUCTIONS_QUERY,
    model= param.MODEL_QUERY,
    output_type=Query,
)