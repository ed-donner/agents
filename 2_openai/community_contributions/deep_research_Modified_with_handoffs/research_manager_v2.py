from agents import Agent, Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from datetime import datetime
import asyncio

# Create handoff-enabled versions of existing agents
planner_handoff_agent = Agent(
    name="PlannerAgent",
    instructions=planner_agent.instructions,
    model=planner_agent.model,
    output_type=WebSearchPlan,
    handoff_description="Create a search plan with multiple search queries for research"
)

search_handoff_agent = Agent(
    name="Search agent", 
    instructions=search_agent.instructions,
    tools=search_agent.tools,
    model=search_agent.model,
    model_settings=search_agent.model_settings,
    handoff_description="Perform web searches and provide summaries"
)

writer_handoff_agent = Agent(
    name="WriterAgent",
    instructions=writer_agent.instructions, 
    model=writer_agent.model,
    output_type=ReportData,
    handoff_description="Synthesize search results into comprehensive reports"
)

email_handoff_agent = Agent(
    name="Email agent",
    instructions=email_agent.instructions,
    tools=email_agent.tools,
    model=email_agent.model,
    handoff_description="Format and send research reports via email"
)

# Deep Research Coordinator instructions describing multi-step process:
deep_research_coordinator_instructions = """You are a Deep Research Coordinator. Your job is to coordinate a research workflow using handoffs.

Given a research query and number of searches, follow these steps. You must always handoff and use the appropritate agents to ge the results. Donot answer directly. repeating, DONOT ANSWER DIRECTLY

1. Hand off to 'PlannerAgent' with the query to get a search plan
Once you get the outcome from step1, go to step 2
2. For each search in the plan, hand off to 'Search agent' with format: 'Search term: [query]\nReason for searching: [reason]'
3. Collect all search results, then hand off to 'WriterAgent' with format: 'Original query: [query]\nSummarized search results: [results]'
4. Finally, hand off to 'Email agent' with the markdown report to send the email

Use handoffs to coordinate between agents. Return the final result."""

# Create the Deep Research Coordinator Agent with proper handoffs
deep_research_coordinator_agent = Agent(
    name="Deep Research Coordinator",
    instructions=deep_research_coordinator_instructions,
    handoffs=[planner_handoff_agent,search_handoff_agent,writer_handoff_agent,email_handoff_agent,],
    model="gpt-4o-mini"
)

class ResearchManager:

    def __init__(self):
        self.coordinator = deep_research_coordinator_agent

    async def run_coordinator(self, query: str, num_searches: int = 5):
        """ Run the deep research coordinator using proper agent handoffs """
        trace_id = gen_trace_id()
        with trace("Deep Research Coordinator Trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            
            yield "Starting Deep Research Coordinator..."
            
            # The coordinator will handle all handoffs automatically
            coordinator_input = f"""Research Query: {query}
Number of searches required: {num_searches}"""
            
            # Let the coordinator agent manage the entire workflow using handoffs
            result = await Runner.run(self.coordinator, coordinator_input)
            
            yield "Deep Research Coordinator workflow complete!"
            yield str(result.final_output)

    # Alias for backward compatibility
    async def run_orchestrator(self, query: str):
        """ Legacy method - redirects to coordinator """
        async for result in self.run_coordinator(query, num_searches=5):
            yield result