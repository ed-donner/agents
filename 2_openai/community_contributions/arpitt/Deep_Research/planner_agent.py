from typing import List

from dotenv import load_dotenv
from agents import Agent
from pydantic import BaseModel, Field
from guardRails import guard_sensitive_topics

load_dotenv(override=True)

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output 3 terms to query for."


class WebSearchItem(BaseModel):
    reason : str = Field("reason why you chose this field")

    query : str = Field('')


class WebSearchList(BaseModel):
    searchList : List[WebSearchItem]


planner_agent = Agent(name='planner_agent',
                      instructions=INSTRUCTIONS,
                      model='gpt-4o-mini',
                      output_type=WebSearchList,
                      input_guardrails=[guard_sensitive_topics])
