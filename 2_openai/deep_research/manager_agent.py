from agents import Agent, ModelSettings
from planner_agent import planner_agent_tool
from search_agent import search_agent_tool
from writer_agent import writer_agent_tool
from evaluator_agent import evaluator_agent_tool, optimizer_agent_tool

MANAGER_INSTRUCTIONS = """You are a Deep Research Manager. Your job is to produce a comprehensive, high-quality research report.

**Workflow:**
1. **Plan**: Use search_planner with the user's (refined) query to get a list of web searches. Plan up to 15–20 searches for the first round.
2. **Search**: For each planned search term, call web_search once. Collect all summaries. You may do at most one additional round of searches (up to 5 more terms) if you discover gaps—use search_planner again with a refined sub-query, then call web_search for each new term.
3. **Write**: Use write_report with the original query and a single text that concatenates all search summaries. Produce a long, detailed report (5–10 pages, 1000+ words).
4. **Evaluate**: Use evaluate_report on the markdown report. If it returns needs_refinement=True, use optimize_report with the report and the suggestions, then treat the improved_markdown_report as the final report.

**Rules:**
- Use only the tools provided; do not make up content.
- Cap total search rounds at 2 (initial plan + at most one extra round of up to 5 searches).
- Always evaluate the report before finalizing. If the evaluator says needs_refinement, always call optimize_report.
- Be thorough: aim for substantive, well-sourced reports that would take several minutes to read."""

manager_agent = Agent(
    name="ResearchManager",
    instructions=MANAGER_INSTRUCTIONS,
    tools=[
        planner_agent_tool,
        search_agent_tool,
        writer_agent_tool,
        evaluator_agent_tool,
        optimizer_agent_tool,
    ],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
