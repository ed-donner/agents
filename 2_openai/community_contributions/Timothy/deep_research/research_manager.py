from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from fact_check_agent import fact_check_agent
from followup_question_agent import followup_question_agent
from report_quality_agent import report_quality_agent
import asyncio

class ResearchManager:
    async def run(self, query: str):
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            search_plan = await self.plan_searches(query)
            yield "Searches planned, starting to search..."
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, fact-checking..."
            fact_check = await self.fact_check(report)
            yield "Fact-checking complete, generating follow-up questions..."
            followups = await self.generate_followups(report)
            yield "Follow-up questions generated, checking report quality..."
            quality = await self.check_quality(report)
            yield "Report quality checked, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield self.compose_final_output(report, fact_check, followups, quality)

    async def plan_searches(self, query: str) -> WebSearchPlan:
        result = await Runner.run(planner_agent, f"Query: {query}")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, input)
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(writer_agent, input)
        return result.final_output_as(ReportData)

    async def fact_check(self, report: ReportData):
        result = await Runner.run(fact_check_agent, report.markdown_report)
        return result.final_output

    async def generate_followups(self, report: ReportData):
        result = await Runner.run(followup_question_agent, report.markdown_report)
        return result.final_output

    async def check_quality(self, report: ReportData):
        result = await Runner.run(report_quality_agent, report.markdown_report)
        return result.final_output

    async def send_email(self, report: ReportData) -> None:
        await Runner.run(email_agent, report.markdown_report)

    def compose_final_output(self, report, fact_check, followups, quality):
        return f"# Report\n{report.markdown_report}\n\n# Fact-Check\n{fact_check}\n\n# Follow-up Questions\n{followups}\n\n# Report Quality\n{quality}"
