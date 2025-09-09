from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from clarifier_agent import clarifier_agent
from evaluator_agent import evaluator_agent, EvaluationFeedback
from optimizer_agent import optimizer_agent, OptimizedReport
import asyncio
import json

class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            
            print("Starting research...")
            search_plan = await self.plan_searches(query)
            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Evaluating report..."
            feedback = await self.evaluate_report(report.markdown_report)
            yield f"Suggestions: {'; '.join(feedback.suggestions)}"
            yield "Optimizing report..."
            improved = await self.optimize_report(report.markdown_report, feedback.suggestions)
            improved_report = ReportData(
                short_summary=report.short_summary,
                follow_up_questions=report.follow_up_questions,
                markdown_report=improved.improved_markdown_report
            )
            yield "Report written" # , sending email...
            # await self.send_email(improved_report)
            yield "Research complete" # Email sent, 
            # yield report.markdown_report
            yield improved_report.markdown_report

    async def get_clarifying_questions(self, query: str) -> list[str]:
        """Generate clarifying questions for a given query"""
        result = await Runner.run(
            clarifier_agent,
            f"Query: {query}"
        )
        return result.final_output.questions

    def refine_query_with_answers(self, original_query: str, selected_answers: list[str]) -> str:
        """Combine original query with user-selected answers for a refined query"""
        if not selected_answers:
            return original_query
        refinement = "\n\nClarification: " + " ".join(selected_answers)
        return original_query + refinement        

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def evaluate_report(self, report_text: str) -> EvaluationFeedback:
        print("Evaluating report...")
        result = await Runner.run(
            evaluator_agent,
            f"Report:\n{report_text}"
        )
        return result.final_output_as(EvaluationFeedback)

    async def optimize_report(self, report_text: str, suggestions: list[str]) -> OptimizedReport:
        print("Optimizing report...")
        input_text = f"Original Report:\n{report_text}\n\nSuggestions for improvement:\n{suggestions}"
        result = await Runner.run(
            optimizer_agent,
            input_text
        )
        return result.final_output_as(OptimizedReport)
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
        return report