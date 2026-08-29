from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from question_refiner_agent import question_refiner_agent, QueryAnalysis
import asyncio

class ResearchManager:
    def __init__(self):
        self.current_query = None
        self.clarification_answers = []

    async def analyze_query(self, query: str) -> QueryAnalysis:
        print("Analyzing query...")
        result = await Runner.run(
            question_refiner_agent,
            f"Query: {query}",
        )
        return result.final_output_as(QueryAnalysis)

    async def run(self, query: str, clarification_answer: str = None, send_email_flag: bool = False, depth: str = "Medium (10 searches)"):
        if clarification_answer:
            self.clarification_answers.append(clarification_answer)
            if len(self.clarification_answers) < 3:
                analysis = await self.analyze_query(query)
                if analysis.needs_clarification:
                    yield f"Clarification needed: {analysis.clarifying_questions[len(self.clarification_answers)]}"
                    return
                query = f"{query}\nClarifications: {'; '.join(self.clarification_answers)}"
            else:
                query = f"{query}\nClarifications: {'; '.join(self.clarification_answers)}"
        else:
            analysis = await self.analyze_query(query)
            if analysis.needs_clarification:
                self.current_query = query
                yield f"Clarification needed: {analysis.clarifying_questions[0]}"
                return

        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            search_plan = await self.plan_searches(query, depth)
            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)

            if send_email_flag:
                yield "Report written, sending email..."
                await self.send_email(report)
                yield "Email sent"
            else:
                yield "Report written (email not sent)."

            yield report.markdown_report

    async def plan_searches(self, query: str, depth: str) -> WebSearchPlan:
        print("Planning searches...")

        depth_map = {
            "Quick Look (5 searches)": 5,
            "Standard (10 searches)": 10,
            "In-Depth (20 searches)": 20,
        }
        how_many = depth_map.get(depth, 10)

        planner_agent.instructions = (
            f"You are a helpful research assistant. Given a query, come up with a set of web searches "
            f"to perform to best answer the query. Output {how_many} terms to query for."
        )

        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )

        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
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
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )
        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
