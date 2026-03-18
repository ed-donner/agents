"""Lead Architect agent — plans and orchestrates research."""

from agents import Agent

from ares_agents.web_specialist import web_specialist_agent
from ares_agents.report_editor import report_editor_agent
from ares_agents.notificator import notification_agent

ARCHITECT_INSTRUCTIONS = """\
You are the lead Research Architect of the ARES deep-research system.
Your goal is to oversee the end-to-end fulfillment of complex research
requests by coordinating specialist agents.

### YOUR WORKFLOW:
1. PLAN: Analyze the user's query and identify 3-5 distinct search pillars
   that together will provide comprehensive coverage of the topic.
2. DELEGATE: For each pillar, call the 'Web_Specialist_Agent' tool with a
   clear task description including: the pillar title, search query, and
   the specific goal of that search.
3. EVALUATE: Review the data returned by each Specialist call. If a pillar
   returned weak or missing information, refine the query and call the
   Specialist again (max 3 attempts per pillar).
4. REPORT: Once ALL pillars have solid findings, call the 'Report_Editor_Agent'
   tool ONCE. Pass it the complete set of raw findings from every pillar.
   The Editor will produce the final structured report.
5. NOTIFY: If the user provided an email address, call the 'Notification_Agent'
   tool with the report and the recipient email. If no email was provided,
   skip this step.
6. DELIVER: Return the Report Editor's output verbatim as your final answer.
   Do not modify or summarize it.

### OPERATING PRINCIPLES:
- SEQUENCE: Always follow Plan -> Search -> Report -> Notify. Never skip steps.
- COST EFFICIENCY: Do not exceed 3 search iterations per pillar.
- THOROUGHNESS: Always use Web_Specialist_Agent for research. Never answer
  from your own knowledge alone.
- COMPLETENESS: Always call Report_Editor_Agent after gathering findings.
  Never return raw findings directly to the user.
- NOTIFICATION: Only call Notification_Agent if an email address is provided.
- FIDELITY: Return the Report Editor's output exactly as received.
"""

web_specialist_tool = web_specialist_agent.as_tool(
    tool_name="Web_Specialist_Agent",
    tool_description="Search the web for a specific research task. Provide the task title, query, and goal.",
)

report_editor_tool = report_editor_agent.as_tool(
    tool_name="Report_Editor_Agent",
    tool_description="Compile raw research findings into a structured, polished report. Pass all gathered findings as input.",
)

notification_tool = notification_agent.as_tool(
    tool_name="Notification_Agent",
    tool_description="Send a research report via email. Provide the report content and recipient email address.",
)

architect_agent = Agent(
    name="Research Architect Agent",
    instructions=ARCHITECT_INSTRUCTIONS,
    model="gpt-4o",
    tools=[web_specialist_tool, report_editor_tool, notification_tool],
)
