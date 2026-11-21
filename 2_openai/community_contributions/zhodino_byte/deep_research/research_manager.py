from dataclasses import dataclass

from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from clarifying_agent import ClarifyingResponse, clarifying_agent, ClarifiedQuestion
import asyncio


@dataclass
class ClarificationRequest:
    questions: list[str]


class ResearchManager:

    async def run(self, query: str):
        """Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            yield f"Starting research. Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            questions = await self.clarify_question(query)
            answers = yield ClarificationRequest(
                questions=[q.question for q in questions.questions]
            )
            clarified_questions = [
                ClarifiedQuestion(question=question, answer=answer)
                for question, answer in zip(questions.questions, answers)
            ]
            search_plan = await self.plan_searches(query, clarified_questions)
            yield f"Searches planned, starting {len(search_plan.searches)} searches..."
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report

    async def clarify_question(self, query: str) -> ClarifyingResponse:
        """Clarify user's question"""
        result = await Runner.run(clarifying_agent, f"Query: {query}")
        return result.final_output

    async def ask_user_for_clarifying(
        self, questions: ClarifyingResponse
    ) -> list[ClarifiedQuestion]:
        """Ask user for the questions from clarifying agent"""

    async def plan_searches(
        self,
        query: str,
        clarified_questions: ClarifiedQuestion,
    ) -> WebSearchPlan:
        """Plan the searches to perform for the query"""
        result = await Runner.run(
            planner_agent, f"Query: {query}, Questions: {clarified_questions}"
        )
        return result.final_output

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Perform the searches to perform for the query"""
        tasks = [self.search(item) for item in search_plan.searches]
        return await asyncio.gather(*tasks)

    async def search(self, item: WebSearchItem) -> str | None:
        """Perform a search for the query"""
        input_message = (
            f"Search term: {item.query}\nReason for searching: {item.reason}"
        )
        result = await Runner.run(search_agent, input_message)
        return result.final_output

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Write the report for the query"""
        input_message = (
            f"Original query: {query}\nSummarized search results: {search_results}"
        )
        result = await Runner.run(writer_agent, input_message)
        return result.final_output

    async def send_email(self, report: ReportData) -> None:
        await Runner.run(email_agent, report.markdown_report)
