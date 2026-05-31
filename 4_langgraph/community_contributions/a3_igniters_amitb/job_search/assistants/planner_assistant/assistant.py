from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from .prompts import SYSTEM_PROMPT
from job_search.config import get_llm, PLANNER_ASSISTANT
from job_search.state import State
from job_search.helper import format_conversation


class JobSearchPlan(BaseModel):
    search_queries: list[str] = Field(description="List of search queries to use when looking for relevant jobs")
    filters: list[str] = Field(description="List of filters to apply on search results based on user preferences")
    summary: str = Field(description="Brief summary of the search strategy to pass to the executor")


def planner_assistant(state: State) -> State:
    conversation = format_conversation(state["messages"])

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=conversation),
    ]

    llm = get_llm().with_structured_output(JobSearchPlan)
    response = llm.invoke(messages)

    plan_message = (
        f"Job search plan:\n"
        f"Search queries: {response.search_queries}\n"
        f"Filters: {response.filters}\n"
        f"Strategy: {response.summary}"
    )

    return {
        "messages": [{"role": "assistant", "content": plan_message}],
        "last_assistant": PLANNER_ASSISTANT,
    }