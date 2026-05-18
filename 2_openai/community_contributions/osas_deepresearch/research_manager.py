from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from clarifier_agent import ClarifierAgent
from query_refiner_agent import refiner_agent, RefinedQuery
import asyncio


class ResearchManager:

    async def generate_clarifying_questions(self, query: str) -> list[dict]:
        """Use the agentic clarifier to decide 0–5 questions, each with predefined answer options."""
        return await ClarifierAgent().run(query)

    async def refine_query(
        self, query: str, clarifications: list[tuple[str, str]]
    ) -> RefinedQuery:
        """Synthesize the original query and Q&A answers into a precise refined query."""
        qa_text = "\n".join(
            f"Q: {q}\nA: {a}" for q, a in clarifications if a and a.strip()
        )
        input_text = f"Original query: {query}\n\nUser clarification answers:\n{qa_text}"
        result = await Runner.run(refiner_agent, input_text)
        return result.final_output_as(RefinedQuery)

    async def run(self, query: str, clarifications: list[tuple[str, str]] | None = None):
        """Run the deep research process, yielding status updates and the final report."""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")

            # Refine the query when the user provided clarification answers
            answered = [
                (q, a) for q, a in (clarifications or []) if a and a.strip()
            ]
            if answered:
                yield "Refining query based on your answers..."
                refined = await self.refine_query(query, answered)
                working_query = refined.refined_query
                if refined.search_constraints:
                    constraints = ", ".join(refined.search_constraints)
                    yield f"Search constraints identified: {constraints}"
            else:
                working_query = query

            search_plan = await self.plan_searches(working_query)
            yield "Searches planned, starting to search..."
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(working_query, search_results)
            yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Plan the searches to perform for the query."""
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Execute all planned searches in parallel."""
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
        """Perform a single web search and return the summarised result."""
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, input)
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Write the final report from the search results."""
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(writer_agent, input)
        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        await Runner.run(email_agent, report.markdown_report)
        print("Email sent")
