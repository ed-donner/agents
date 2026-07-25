from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio

from clarification_agent import clarification_agent
from query_refiner_agent import query_refiner_agent
from evaluator_agent import evaluator_agent


# constants
MAX_ITERATIONS = 3
MAX_SEARCHES = 12
MAX_CLARIFICATIONS = 2


class ResearchManager:

    def __init__(self):
        self.previous_queries = set()
        self.total_searches = 0

    async def run(self, query: str, answers: str):

        trace_id = gen_trace_id()

        with trace("Research trace", trace_id=trace_id):

            yield f"Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            # STEP 1: Clarification
            clarifications = await self.get_clarifications(query)
            yield f"Clarifying questions:\n{clarifications}"

            # STEP 2: Refine query
            refined_query = await self.refine_query(query, answers)
            yield f"Refined query:\n{refined_query}"

            iteration = 0
            all_search_results = []
            report = None

            while iteration < MAX_ITERATIONS:

                yield f"\n--- Iteration {iteration + 1} ---"

                # STEP 3: Plan
                plan = await self.plan_searches(refined_query)

                # STEP 4: Filter duplicate searches
                filtered_items = []
                for item in plan.searches:
                    if item.query not in self.previous_queries:
                        filtered_items.append(item)
                        self.previous_queries.add(item.query)

                if not filtered_items:
                    yield "No new searches to perform."
                    break

                # Enforce search cap
                remaining_budget = MAX_SEARCHES - self.total_searches
                filtered_items = filtered_items[:remaining_budget]

                if not filtered_items:
                    yield "Search budget exhausted."
                    break

                # STEP 5: Execute searches
                results = await self.perform_searches(filtered_items)
                self.total_searches += len(filtered_items)
                all_search_results.extend(results)

                yield f"Completed {self.total_searches} searches total."

                # STEP 6: Write report
                report = await self.write_report(refined_query, all_search_results)

                # STEP 7: Evaluate
                evaluation = await self.evaluate(report)

                yield f"Quality Score: {evaluation.quality_score}"

                if evaluation.is_sufficient:
                    yield "Report is sufficient. Stopping iterations."
                    break

                # STEP 8: Decide next step
                actions = evaluation.recommended_actions

                if "refine_query" in actions:
                    refined_query = await self.refine_query(
                        refined_query,
                        evaluation.missing_areas
                    )
                    yield "Refined query based on evaluator feedback."

                elif "more_search" in actions:
                    # Light augmentation (controlled)
                    refined_query += " " + " ".join(evaluation.new_search_queries[:2])
                    yield "Expanding search scope."

                elif "ask_user" in actions and iteration < MAX_CLARIFICATIONS:
                    followups = evaluation.missing_areas[:3]
                    yield f"Need more clarification: {followups}"
                    # For now simulate
                    refined_query = await self.refine_query(refined_query, followups)

                iteration += 1

            # FINAL OUTPUT
            if report:
                yield "\n=== FINAL REPORT ===\n"
                yield report.markdown_report

                # Optional: send email
                await self.send_email(report)

            else:
                yield "Failed to generate report."

    # -----------------------
    # Helper Methods
    # -----------------------

    async def plan_searches(self, query: str) -> WebSearchPlan:
        result = await Runner.run(planner_agent, f"Query: {query}")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, items: list[WebSearchItem]) -> list[str]:
        tasks = [asyncio.create_task(self.search(item)) for item in items]
        results = []

        for task in asyncio.as_completed(tasks):
            result = await task
            if result:
                results.append(result)

        return results

    async def search(self, item: WebSearchItem) -> str | None:
        try:
            result = await Runner.run(
                search_agent,
                f"Search term: {item.query}\nReason: {item.reason}"
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, results: list[str]) -> ReportData:
        result = await Runner.run(
            writer_agent,
            f"Query: {query}\nResults: {results}"
        )
        return result.final_output_as(ReportData)

    async def evaluate(self, report: ReportData):
        result = await Runner.run(
            evaluator_agent,
            report.markdown_report
        )
        return result.final_output

    async def get_clarifications(self, query: str):
        result = await Runner.run(
            clarification_agent,
            f"Query: {query}"
        )
        return result.final_output.questions

    async def refine_query(self, query: str, answers):
        result = await Runner.run(
            query_refiner_agent,
            f"Query: {query}\nAnswers: {answers}"
        )
        return result.final_output.refined_query

    async def send_email(self, report: ReportData):
        await Runner.run(email_agent, report.markdown_report)
