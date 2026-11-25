from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan, clarifying_agent, ClarifyingQuestionsList
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio
import gradio as gr


class ResearchManager:

    async def run(self, query: str, clarifying_q: str, clarifying_a: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"Starting research. Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            if not clarifying_q:
                questions = await self.clac_clarifying_qs(query)

                yield (
                    questions, 
                    questions,
                    gr.update(visible=True, value=""),
                    gr.update(visible=True), 
                    f"Now please answere the questions.\n Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
                return

            yield (
            clarifying_q,
            clarifying_q,
            gr.update(),
            gr.update(),
            "Planning and Analyzing",
        )
            search_plan = await self.plan_searches(query, clarifying_q, clarifying_a)
            search_results = await self.perform_searches(search_plan)
            report = await self.write_report(query, search_results)
            yield ("",
                clarifying_q,
                gr.update(visible=False),
                gr.update(visible=False),
                report.markdown_report)

    async def clac_clarifying_qs(self, query: str)-> ClarifyingQuestionsList:
        """ Came up with 3 clarifying qestions """
        result = await Runner.run(clarifying_agent, f"Query: {query}")
        result = "\n".join(f"{index}. {item.question}" for index, item in enumerate(result.questions, start=1))
        return result.final_output
    
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