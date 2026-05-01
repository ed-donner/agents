from agents import Agent, Runner, trace, gen_trace_id
from clarifier_agent import clarifier_agent, ClarifyingQuestions
from planner_agent import planner_agent
from search_agent import search_agent
from writer_agent import writer_agent, ReportData
from email_agent import email_agent

# --- Agents-as-Tools ---
# The planner and search agents are wrapped as tools the manager can call.
# Their outputs return to the manager so it can orchestrate the next step.
planner_tool = planner_agent.as_tool(
    tool_name="plan_searches",
    tool_description="Given a research query and clarifications, create a targeted search plan with multiple search terms.",
)

search_tool = search_agent.as_tool(
    tool_name="web_search",
    tool_description="Search the web for a given term and return a concise summary of the results.",
)

# --- Manager Agent (orchestrator) ---
INSTRUCTIONS = """You are a research manager that orchestrates a deep research workflow.

You have two tools and one handoff available:

**Tools (agents-as-tools):**
- plan_searches: Give it the full query + clarifications. It returns a structured search plan.
- web_search: Give it a single search term and reason. It returns a summary. Call this once 
  per search item from the plan (you can call multiple in parallel).

**Handoff:**
- WriterAgent: Once all searches are complete, hand off to the writer with the original query, 
  clarifications, and all search summaries. The writer will produce the final report.

**Your workflow:**
1. Call plan_searches with the query and clarification Q&A to get a targeted search plan.
2. For each search item in the plan, call web_search with the search term and reason.
   Call all searches in parallel for efficiency.
3. Once you have all search summaries, hand off to WriterAgent. In your handoff message, 
   include the original query, the clarification Q&A, and all the search summaries so the 
   writer has full context.

Do NOT write the report yourself — always hand off to WriterAgent for that."""

research_manager_agent = Agent(
    name="ResearchManager",
    instructions=INSTRUCTIONS,
    model="gpt-4o",
    tools=[planner_tool, search_tool],
    handoffs=[writer_agent],
)


async def run_clarifier(query: str) -> list[str]:
    """Run the clarifier agent to generate 3 clarifying questions."""
    result = await Runner.run(clarifier_agent, f"Research query: {query}")
    output = result.final_output_as(ClarifyingQuestions)
    return output.questions


async def run_research(query: str, q1: str, a1: str, q2: str, a2: str, q3: str, a3: str):
    """Run the full research pipeline: manager (plan + search + handoff to writer), then email."""
    trace_id = gen_trace_id()

    with trace("Deep Research v2", trace_id=trace_id):
        trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        print(f"View trace: {trace_url}")
        yield f"**Starting research...**\n\n[View trace]({trace_url})\n\n"

        clarification_context = (
            f"Q: {q1}\nA: {a1}\n\n"
            f"Q: {q2}\nA: {a2}\n\n"
            f"Q: {q3}\nA: {a3}"
        )

        input_text = (
            f"Research query: {query}\n\n"
            f"Clarifying Q&A:\n{clarification_context}"
        )

        yield "**Planning searches...**\n\n"

        result = await Runner.run(research_manager_agent, input_text)

        report = result.final_output_as(ReportData)
        yield f"**Report complete. Sending email...**\n\n"

        await Runner.run(email_agent, report.markdown_report)

        yield f"**Email sent!**\n\n---\n\n{report.markdown_report}"
