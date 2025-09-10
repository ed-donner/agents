from tools.tool_wrapper import tool_from_agent
from schema import ReportData


REPORT_INSTRUCTIONS = """
Role:
- You are a senior researcher.

Task:
- Write a cohesive research report that directly answers the initial query,
  using only the executed search plan results provided.

Input:
- `executed_plan`: the executed search plan results with queries and summaries.
- `initial_query`: the original research query string.

Operational rules:
- Structure the report with an introduction, body, and conclusion.
- Synthesize insights clearly and logically.
- Stay faithful to the executed plan data (do not invent information).
- Length: 500–700 words.
- Fill 'markdown_report' with the final report in markdown format.

Output:
- A ReportData schema.
"""

report_writer_tool = tool_from_agent(
    agent_name="ReportWriter",
    agent_instructions=REPORT_INSTRUCTIONS,
    output_type=ReportData,
    tool_name="report_writer",
    tool_description="Consumes the initial research query and an ExecutedSearchPlan, and produces a structured final report."
)
