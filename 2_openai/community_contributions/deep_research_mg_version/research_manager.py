from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan, clarifying_agent, ClarifyingQuestionsList
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio

class ClarifyingQuestions:
    async def run(self, query: str):
        """ Came up with 5 clarifying qestions """
        trace_id = gen_trace_id()
        with trace("Clarifying trace", trace_id=trace_id):
            yield f"Starting Clarifying. Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            result = await Runner.run(clarifying_agent, f"Query: {query}")
            questions = "\n".join(
                f"{index}. {item.question}"
                for index, item in enumerate(result.final_output.questions, start=1)
            )
            yield questions

class ResearchManager:

    async def run(self, query: str, clarify_q: str, clarify_a: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            yield f"Starting research. Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            search_plan = await self.plan_searches(query, clarify_q, clarify_a)
            yield f"Searches planned, starting {len(search_plan.searches)} searches..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."
            # await self.send_email(report)
            # yield "Email sent, research complete"
            yield report.markdown_report

    async def plan_searches(self, query: str, clarify_q: str, clarify_a: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        result = await Runner.run(planner_agent, f"Query: {query}, clarifying questions: {clarify_q}, clarifying answere: {clarify_a}")
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