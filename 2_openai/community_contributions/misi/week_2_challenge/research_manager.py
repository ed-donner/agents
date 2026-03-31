from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from printer_agent import printer_agent
from clarification_agent import (
    clarification_agent,
    refinement_agent,
    ClarificationQuestions,
    RefinedQuery,
)
import asyncio


class ResearchManager:

    async def run(self, query: str):
        """Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(
                f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            )
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            yield "Planning searches..."
            search_plan = await self.plan_searches(query)
            yield "Searches planned, starting to search..."
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, printing report..."
            await self.print_report(report)
            yield "Report printed, research complete"
            yield report.markdown_report

    async def get_clarification_questions(self, query: str) -> ClarificationQuestions:
        """Generate 3 clarification questions for the user's research topic."""
        print("Generating clarification questions...")
        result = await Runner.run(
            clarification_agent,
            f"User query: {query}",
        )
        print("Finished generating clarification questions")
        return result.final_output_as(ClarificationQuestions)

    async def refine_query(
        self, query: str, questions: list[str], answers: list[str]
    ) -> str:
        """Combine the original query and clarification answers into one refined query."""
        print("Refining query...")
        numbered_questions = "\n".join(
            f"{index}. {question}" for index, question in enumerate(questions, start=1)
        )
        numbered_answers = "\n".join(
            f"{index}. {answer}" for index, answer in enumerate(answers, start=1)
        )
        result = await Runner.run(
            refinement_agent,
            (
                f"Original query: {query}\n"
                f"Clarification questions:\n{numbered_questions}\n"
                f"User answers:\n{numbered_answers}"
            ),
        )
        print("Finished refining query")
        return result.final_output_as(RefinedQuery).refined_query

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Plan the searches to perform for the query"""
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Perform the searches to perform for the query"""
        print("Searching...")
        num_completed = 0
        tasks = [
            asyncio.create_task(self.search(item)) for item in search_plan.searches
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

    async def search(self, item: WebSearchItem) -> str | None:
        """Perform a search for the query"""
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
        """Write the report for the query"""
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def print_report(self, report: ReportData) -> None:
        print("Printing report...")
        result = await Runner.run(
            printer_agent,
            report.markdown_report,
        )
        print("Report printed")
        return report
