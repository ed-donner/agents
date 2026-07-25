from agents import Agent
from planner_agent import planner_tool
from search_agent import search_tool
from writer_agent import writer_tool
from evaluator_agent import evaluator_tool


ORCHESTRATOR_PROMPT = """
You are a deep research orchestrator. You are given a refined, specific research query.

Follow these steps in order:

1. PLAN - Call plan_searches with the query.

2. SEARCH - Call perform_search for every search query returned. Do not skip any.

3. WRITE - Call write_report with the query and all search results.

4. EVALUATE - Call evaluate_report with the original query and the written report.
   - If passes=True, return the final report.
   - If passes=False, rewrite ONCE using the feedback, then return that version regardless.

Never evaluate more than twice total. Never rewrite more than once.
Always complete all steps in order.
"""

orchestrator_agent = Agent(
    name="Orchestrator Agent",
    instructions=ORCHESTRATOR_PROMPT,
    tools=[
        planner_tool,
        search_tool,
        writer_tool,
        evaluator_tool,
    ],
    model="gpt-4o",
)