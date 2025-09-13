from agents import Runner, trace, gen_trace_id, function_tool, Agent
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from clarifier import clarifier_agent
import asyncio

# === Define Orchestrator Agent (Lab 2 style) ===
orchestrator_agent = Agent(
    name="Research Orchestrator",
    instructions="",  
    tools=[],         
    model="gpt-4o-mini",
    handoff_description="Coordinate clarifier, planner, search, writer, and email in sequence."
)

class ResearchManager:
    def __init__(self):
        self.clarifier_used = False  

        # Register helpers as tools but keep them callable
        self.tools = [
            function_tool(self.clarify_query),
            function_tool(self.plan_searches),
            function_tool(self.perform_searches),
            function_tool(self.write_report),
            function_tool(self.send_email),
        ]

    # === Plain async methods (callable directly in Gradio) ===
    async def clarify_query(self, query: str):
        """Asks clarifying questions to better understand the research query."""
        if not self.clarifier_used:
            result = await Runner.run(clarifier_agent, query)
            self.clarifier_used = True
            return result.final_output.questions
        return []

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Creates a research plan with recommended search steps."""
        result = await Runner.run(planner_agent, f"Query: {query}")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Looks up information for each step in the research plan."""
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            res = await task
            if res:
                results.append(res)
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """Perform a single search query."""
        try:
            result = await Runner.run(search_agent, f"Search term: {item.query}\nReason: {item.reason}")
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Drafts a research report based on all findings."""
        result = await Runner.run(writer_agent, f"Original query: {query}\nSummarized results: {search_results}")
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData) -> None:
        """Formats and sends the final research report via email."""
        await Runner.run(email_agent, report.markdown_report)
        return report

    async def orchestrator(self, query: str, clarifications: str = ""):
        orchestrator_agent.instructions = """
        You are the Orchestrator for the Deep Research process. 
        You receive a research query (and optional clarifications) and manage the research workflow.

        The required order of execution is:
        1. Clarifier (only once)
        2. Planner
        3. Search
        4. Writer
        5. Email

        Rules:
        - Always follow this order.
        - Pass outputs as inputs to the next.
        - Clarifier runs only once.
        - Ensure Email is the final tool.
        - Retry steps if outputs are empty.
        """
        orchestrator_agent.tools = self.tools
        return await Runner.run(
            orchestrator_agent,
            f"Research query: {query}\nClarifications: {clarifications}"
        )

    async def run(self, query: str, clarifications: str = ""):
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            result = await self.orchestrator(query, clarifications)
            return result.final_output
