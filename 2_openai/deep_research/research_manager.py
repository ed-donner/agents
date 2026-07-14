from agents import Runner, trace, gen_trace_id
from clarify_agent import clarify_agent, ClarifyQuestion
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio

class ResearchManager:

    async def run_clarify(self, query: str) -> list[ClarifyQuestion]:
        """ Run the clarify process """
        clarify_queries = await self.clarify_query(query)
        return clarify_queries

    async def run(self, query: str, questions: list[ClarifyQuestion]|None = None):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            yield f"Starting research. Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            search_plan = await self.plan_searches(query, questions)
            yield f"Searches planned, starting {len(search_plan.searches)} searches..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report

    async def clarify_query(self, query: str) -> list[ClarifyQuestion]:
        """ Clarify the query """
        result = await Runner.run(clarify_agent, f"Query: {query}")
        return result.final_output

    async def plan_searches(self, query: str, questions: list[ClarifyQuestion]) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        clarify = ""
        for question in questions:
            clarify += f"Question: {question.question}\n"
            clarify += f"Answer: {question.answer}\n"
        result = await Runner.run(planner_agent, f"Query: {query}\n Clarifications:\n{clarify}")
        return result.final_output

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        tasks = [self.search(item) for item in search_plan.searches]
        return await asyncio.gather(*tasks)

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input_message = f"Search term: {item.query}\nReason for searching: {item.reason}"
        result = await Runner.run(search_agent, input_message)
        return result.final_output

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        input_message = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(writer_agent, input_message)
        return result.final_output
    
    async def send_email(self, report: ReportData) -> None:
        await Runner.run(email_agent, report.markdown_report)