from __future__ import annotations

import logging
from typing import List
from pydantic import BaseModel, Field, constr, field_validator, model_validator
from agents import Agent

logger = logging.getLogger("planner_agent")
logger.addHandler(logging.NullHandler())

HOW_MANY_SEARCHES = 2

INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."

# Constrained text types (keeps LLM outputs short and safe)
ShortText = constr(strip_whitespace=True, min_length=5, max_length=240)
QueryText = constr(strip_whitespace=True, min_length=3, max_length=120)


class WebSearchItem(BaseModel):
    query: QueryText = Field(..., description="Search term to use for the web search.")
    reason: ShortText = Field(..., description="One-line rationale for why this search is important.")

    @field_validator("query")
    @classmethod
    def validate_query(cls, query: str) -> str:
        # Disallow embedded newlines and obviously malformed queries
        if "\n" in query or "\r" in query:
            raise ValueError("query must be a single-line search term.")
        # Avoid extremely generic single-word queries unless allowed by context (heuristic)
        if len(query.split()) == 1 and len(query) < 4:
            raise ValueError("query is too short; prefer a 2-4 word search phrase for precision.")
        return query

class WebSearchPlan(BaseModel):
    searches: List[WebSearchItem] = Field(..., description="Exactly N web searches (query + reason).")

    @model_validator(mode="after")
    def enforce_search_count_and_uniqueness(self) -> "WebSearchPlan":
        if len(self.searches) != HOW_MANY_SEARCHES:
            raise ValueError(f"Exactly {HOW_MANY_SEARCHES} searches are required.")
        # Enforce distinct queries
        queries = [search_item.query.lower() for search_item in self.searches]
        if len(set(queries)) != len(queries):
            raise ValueError("Search queries must be unique.")
        return self

def validate_model_output(raw: dict) -> WebSearchPlan:
    """
    Validate and parse a raw dict produced by the LLM into WebSearchPlan.
    Raises pydantic.ValidationError on invalid output.
    """
    logger.debug("Validating planner model output")
    return WebSearchPlan.model_validate(raw)
    
planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)