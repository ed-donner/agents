from agents import Agent, Runner, RunHooks, function_tool
from planner_agent import planner_agent
from search_agent import search_agent
from writer_agent import writer_agent
from evaluator_agent import evaluator_agent
from email_agent import email_agent
import os
from dotenv import load_dotenv

load_dotenv(override=True)
MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "gpt-5.4-mini")


@function_tool
async def send_report_email(report_markdown: str) -> str:
    """Send the final research report as an email. Returns a status string and never raises,
    so a missing email setup does not break the research run."""
    try:
        await Runner.run(email_agent, report_markdown)
        return "Email sent."
    except Exception as e:
        return f"Email step skipped (no working email setup): {e}"


# Expose each specialist agent as a tool the manager can choose to call (agents-as-tools, no handoffs).
planner_tool = planner_agent.as_tool(
    tool_name="plan_searches",
    tool_description="Given the query and any clarifications, return a list of web search terms with reasons.",
)
search_tool = search_agent.as_tool(
    tool_name="web_search",
    tool_description="Search the web for a single term and return a concise summary. Call once per term.",
)
evaluator_tool = evaluator_agent.as_tool(
    tool_name="evaluate_alignment",
    tool_description="Judge whether the gathered summaries satisfy the query and clarifications; returns alignment and feedback.",
)
writer_tool = writer_agent.as_tool(
    tool_name="write_report",
    tool_description="Write the final detailed markdown report from the query, clarifications and summaries.",
)

INSTRUCTIONS = """You are a Research Manager. Produce a report that answers the user's query and
respects their clarifications, using your tools. You choose how to use them, but stay within the limits
below so that you finish promptly.

Your tools:
- plan_searches: turn the query and clarifications into a list of search terms.
- web_search: run a single web search and get back a summary. Call it once per term.
- evaluate_alignment: check whether the summaries so far satisfy the query and the user's clarifications.
- write_report: produce the final markdown report.
- send_report_email: email the finished report.

Follow this process and respect the limits:
1. Call plan_searches once to get the search terms.
2. Call web_search for each term. Never repeat a search you have already run.
3. Call evaluate_alignment once. If it reports misalignment, run a few more targeted searches based on
   its feedback, then call evaluate_alignment one more time. Use evaluate_alignment at most twice in total.
4. Call write_report once to produce the report.
5. Call send_report_email once to send the report. This step is mandatory: the task is not
   complete until send_report_email has been called.
6. Stop. Do not call any tools after sending the email.

Always take the user's clarifications (scope, audience, time frame, depth, focus) into account.
Your final output must be the complete markdown report returned by write_report."""

research_manager_agent = Agent(
    name="Research Manager",
    instructions=INSTRUCTIONS,
    tools=[planner_tool, search_tool, evaluator_tool, writer_tool, send_report_email],
    model=MODEL_NAME,
)


def build_manager_input(query: str, clarifications: str = "") -> str:
    """Assemble the single input string handed to the manager agent."""
    parts = [f"Research query: {query}"]
    if clarifications:
        parts.append(clarifications)
    parts.append("Carry out the research and produce the final report.")
    return "\n\n".join(parts)


class ConsoleLogHooks(RunHooks):
    """Logs the manager agent's tool calls to the console so a long run is not silent,
    and records which tools were called so code can verify the email step happened."""

    def __init__(self):
        self.tool_count = 0
        self.called_tools = set()

    async def on_agent_start(self, context, agent):
        print(f"[manager] {agent.name} started", flush=True)

    async def on_tool_start(self, context, agent, tool):
        self.tool_count += 1
        self.called_tools.add(tool.name)
        print(f"[manager] step {self.tool_count}: calling '{tool.name}'...", flush=True)

    async def on_tool_end(self, context, agent, tool, result):
        preview = " ".join(str(result).split())[:140]
        print(f"[manager] step {self.tool_count}: '{tool.name}' done -> {preview}", flush=True)

    async def on_agent_end(self, context, agent, output):
        print(f"[manager] {agent.name} finished after {self.tool_count} tool calls", flush=True)
