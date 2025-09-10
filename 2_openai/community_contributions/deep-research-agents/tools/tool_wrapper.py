from agents import Agent
from typing import Type, Union
from schema import ExecutedSearchPlan, Question, ReportData, WebSearchPlan
from agents.tool import Tool


def tool_from_agent(
    agent_name: str,
    agent_instructions: str,
    output_type: Type[Union[Question, WebSearchPlan, ExecutedSearchPlan, ReportData]],
    tool_name: str,
    tool_description: str,
    **kwargs
    ) -> Tool:
    agent = Agent(
        name=agent_name,
        instructions=agent_instructions,
        model="gpt-5-mini",
        output_type=output_type,
        **kwargs
    )
    return agent.as_tool(
        tool_name,
        tool_description
    )
