"""Week 2 (OpenAI Agents SDK) deliverable — a minimal deep-research agent.

Shows the SDK's core moves: an Agent with a Pydantic `output_type` (the planner returns structured
searches), agents run in parallel with asyncio.gather, a hosted WebSearchTool, and the whole run
wrapped in one trace() for observability. Flow: plan -> search (parallel) -> write.

Run: uv run python deep_research.py "your research question"
     (needs OPENAI_API_KEY; WebSearchTool bills per search)
"""
import asyncio
import sys

from agents import Agent, Runner, WebSearchTool, trace
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(override=True)
HOW_MANY = 3


class Search(BaseModel):
    query: str
    reason: str


class SearchPlan(BaseModel):
    searches: list[Search]


planner = Agent(
    name="Planner",
    instructions=f"You plan web research. Given a query, output {HOW_MANY} focused web searches "
                 "that together answer it.",
    model="gpt-4o-mini",
    output_type=SearchPlan,                      # structured output — guaranteed schema
)

searcher = Agent(
    name="Searcher",
    instructions="Search the web for the given term and reason. Reply with a concise 2-3 paragraph "
                 "summary (under 300 words) of what you found. No preamble.",
    model="gpt-4o-mini",
    tools=[WebSearchTool(search_context_size="low")],   # hosted OpenAI web-search tool
)

writer = Agent(
    name="Writer",
    instructions="You are a research writer. Given the original query and a set of search summaries, "
                 "write a cohesive markdown report (a few hundred words) that answers the query.",
    model="gpt-4o-mini",
)


async def research(query: str) -> str:
    with trace("Deep research"):                                     # one trace for the whole run
        plan = (await Runner.run(planner, query)).final_output       # -> SearchPlan (structured)
        summaries = await asyncio.gather(*[                          # searches run concurrently
            Runner.run(searcher, f"Term: {s.query}\nReason: {s.reason}") for s in plan.searches
        ])
        findings = "\n\n".join(r.final_output for r in summaries)
        report = await Runner.run(writer, f"Query: {query}\n\nFindings:\n{findings}")
        return report.final_output


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What are the main agentic AI frameworks in 2025?"
    print(asyncio.run(research(q)))
