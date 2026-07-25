from agents import Runner, trace, gen_trace_id, Agent
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio


class ResearchManager:

    async def run(self, query: str):
        """Run the deep research process"""

        trace_id = gen_trace_id()

        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            # --- small addition: clarify query ---
            yield "Clarifying query..."
            query = await self.clarify_query(query)

            print("Starting research...")

            all_results = []
            max_rounds = 2  

            for i in range(max_rounds):
                yield f"Planning searches (round {i+1})..."

                search_plan = await self.plan_searches(query)

                yield "Running searches..."
                results = await self.perform_searches(search_plan)

                all_results.extend(results)

                if i < max_rounds - 1:
                    should_continue = await self.should_continue(query, all_results)
                    if not should_continue:
                        break

                    yield "Refining query..."
                    query = await self.refine_query(query, all_results)

            yield "Writing report..."
            report = await self.write_report(query, all_results)

            yield "Sending email..."
            await self.send_email(report)

            yield "Done"
            yield report.markdown_report

   #Clarifier helper function

    async def clarify_query(self, query: str) -> str:
        agent = Agent(
            name="clarifier",
            instructions="""
            Ask 3 short clarifying questions internally and improve the query.
            Return only the improved query.
            """,
            model="openai/gpt-4o-mini",
        )

        result = await Runner.run(agent, query)
        return result.final_output

    async def should_continue(self, query: str, results: list[str]) -> bool:
        agent = Agent(
            name="decision",
            instructions="""
            Based on current results, decide if more research is needed.
            Answer only yes or no.
            """,
            model="openai/gpt-4o-mini",
        )

        result = await Runner.run(agent, f"{query}\n{results}")
        return "yes" in result.final_output.lower()

    async def refine_query(self, query: str, results: list[str]) -> str:
        agent = Agent(
            name="refiner",
            instructions="""
            Slightly improve the query based on findings.
            Keep it short and more specific.
            """,
            model="openai/gpt-4o-mini",
        )

        result = await Runner.run(agent, f"{query}\n{results}")
        return result.final_output

   
    async def plan_searches(self, query: str) -> WebSearchPlan:
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        print("Searching...")
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]

        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)

        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        input = f"Search term: {item.query}\nReason: {item.reason}"

        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        print("Writing report...")
        input = f"Query: {query}\nResults: {search_results}"

        result = await Runner.run(
            writer_agent,
            input,
        )

        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData):
        print("Sending email...")
        await Runner.run(
            email_agent,
            report.markdown_report,
        )