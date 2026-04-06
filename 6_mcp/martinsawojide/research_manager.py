import asyncio
from contextlib import AsyncExitStack

from agents import Runner
from agents.mcp import MCPServerStdio

from custom_tracing import custom_trace
from email_agent import build_email_agent
from mcp_stdio import mcp_stdio_params
from planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from search_agent import build_search_agent
from writer_agent import ReportData, writer_agent

TAVILY_MCP_TIMEOUT = 120
EMAIL_MCP_TIMEOUT = 90


class ResearchManager:

    async def run(self, query: str):
        """Run deep research, yielding status updates and the final report."""
        tavily_params = mcp_stdio_params("tavily_mcp_server.py")
        email_params = mcp_stdio_params("email_mcp_server.py")

        async with AsyncExitStack() as stack:
            tavily_server = await stack.enter_async_context(
                MCPServerStdio(
                    params=tavily_params,
                    client_session_timeout_seconds=TAVILY_MCP_TIMEOUT,
                )
            )
            email_server = await stack.enter_async_context(
                MCPServerStdio(
                    params=email_params,
                    client_session_timeout_seconds=EMAIL_MCP_TIMEOUT,
                )
            )

            search_agent = build_search_agent([tavily_server])
            email_agent = build_email_agent([email_server])
            search_lock = asyncio.Lock()

            async with custom_trace("Research trace", kind="CHAIN"):
                print("Starting research...")
                search_plan = await self.plan_searches(query)
                yield "Searches planned, starting to search..."
                search_results = await self.perform_searches(
                    search_plan, search_agent, search_lock
                )
                yield "Searches complete, writing report..."
                report = await self.write_report(query, search_results)
                yield "Report written, sending email..."
                await self.send_email(report, email_agent)
                yield "Email sent, research complete"
                yield report.markdown_report

    async def plan_searches(self, query: str) -> WebSearchPlan:
        print("Planning searches...")
        async with custom_trace("plan_searches", kind="AGENT", query=query):
            result = await Runner.run(
                planner_agent,
                f"Query: {query}",
            )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(
        self,
        search_plan: WebSearchPlan,
        search_agent,
        search_lock: asyncio.Lock,
    ) -> list[str]:
        print("Searching...")
        async with custom_trace(
            "perform_searches", kind="CHAIN", num_searches=len(search_plan.searches)
        ):
            num_completed = 0
            tasks = [
                asyncio.create_task(
                    self.search(item, search_agent, search_lock)
                )
                for item in search_plan.searches
            ]
            results = []
            for task in asyncio.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
                print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem, search_agent, lock: asyncio.Lock) -> str | None:
        input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
        async with custom_trace("search", kind="AGENT", query=item.query):
            try:
                async with lock:
                    result = await Runner.run(
                        search_agent,
                        input_text,
                    )
                return str(result.final_output)
            except Exception:
                return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        print("Thinking about report...")
        async with custom_trace("write_report", kind="AGENT", query=query):
            input_text = f"Original query: {query}\nSummarized search results: {search_results}"
            result = await Runner.run(
                writer_agent,
                input_text,
            )
        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData, email_agent) -> None:
        print("Writing email...")
        async with custom_trace("send_email", kind="AGENT"):
            await Runner.run(
                email_agent,
                report.markdown_report,
            )
        print("Email sent")
