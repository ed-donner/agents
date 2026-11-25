import asyncio
import os
from typing import Literal
from agents import Agent, Runner, function_tool, gen_trace_id, trace
from pydantic import BaseModel
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan, clarifying_agent, ClarifyingQuestionsList
from writer_agent import writer_agent, ReportData
import gradio as gr

MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")

class ManagerDecision(BaseModel):
  status: Literal["needs_clarification", "completed"]
  content: str


@function_tool
async def clac_clarifying_qs(query: str)-> ClarifyingQuestionsList:
    """ Came up with 3 clarifying qestions """
    result = await Runner.run(clarifying_agent, f"Query: {query}")
    result = "\n".join(f"{index}. {item.question}" for index, item in enumerate(result.questions, start=1))
    return result.final_output

@function_tool
async def plan_searches_and_perform(query: str, clarify_q: str, clarify_a: str) -> WebSearchPlan:
    """ Plan the searches to perform for the query + Perform the searches to perform for the query """
    result = await Runner.run(planner_agent, f"Query: {query}, clarifying questions: {clarify_q}, clarifying answere: {clarify_a}")
    searches = result.final_output
    tasks = [search(item) for item in searches]
    return await asyncio.gather(*tasks)

async def search(item: WebSearchItem) -> str | None:
    """ Perform a search for the query """
    input_message = f"Search term: {item.query}\nReason for searching: {item.reason}"
    result = await Runner.run(search_agent, input_message)
    return result.final_output

@function_tool
async def write_report(query: str, search_results: list[str]) -> ReportData:
    """ Write the report for the query """
    input_message = f"Original query: {query}\nSummarized search results: {search_results}"
    result = await Runner.run(writer_agent, input_message)
    return result.final_output


manager_agent = Agent(
        name="ResearchOrchestrator",
        instructions=(
            "You manage a deep research workflow.\n1. If the user's query"
            " needs clarification (or if previous answers are still unclear),"
            " call `get_clarifying_questions`, set status='needs_clarification',"
            " put the questions in `content`, and stop to wait for the user.\n2."
            " Once you have enough information (either immediately, or after"
            " receiving answers), call `execute_research_and_report` with the"
            " original query, the questions asked, and the user's answers. Then"
            " set status='completed' and put the exact markdown report in"
            " `content`."
        ),
        tools = [clac_clarifying_qs, plan_searches_and_perform, write_report],
        output_type=ManagerDecision,
    )

async def run(query: str, history_state: list, clarifying_a: str, trace_id: str):
      """Run the agent-orchestrated research process."""
      with trace("Research trace", trace_id=trace_id):
        trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        print(f"Starting research. Trace: {trace_url}")

        user_msg = clarifying_a if history_state else query
        current_input = history_state + [{"role": "user", "content": user_msg}]

        result = Runner.run_streamed(manager_agent, input=current_input)

        async for event in result.stream_events():
          if (
              event.type == "run_item_stream_event"
              and event.item.type == "tool_call_item"
          ):
            tool_name = event.item.raw_item.name
            yield (
                history_state,
                gr.update(),
                gr.update(),
                gr.update(),
                f"Running tool: **{tool_name}**...\nTrace: {trace_url}",
            )

        decision: ManagerDecision = result.final_output
        updated_history = result.to_input_list()

        if decision.status == "needs_clarification":
          yield (
              updated_history,
              decision.content,
              gr.update(visible=True, value=""),
              gr.update(visible=True),
              f"Now please answer the questions.\nTrace: {trace_url}",
          )

        elif decision.status == "completed":
          yield (
              [],
              gr.update(),
              gr.update(visible=False, value=""),
              gr.update(visible=False),
              decision.content,
          )