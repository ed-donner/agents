from agents import Runner, trace, gen_trace_id, OutputGuardrailTripwireTriggered, InputGuardrailTripwireTriggered
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from clarifying_agent import clarifying_agent
import asyncio

class ResearchManager:

    async def start_research(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            print("Checking research topic appropriateness and starting research...")
            yield "Checking research topic appropriateness..."

            try:
                search_plan = await self.plan_searches(query)
            except InputGuardrailTripwireTriggered as e:
                # Input guardrail blocked the research topic
                guardrail_info = e.guardrail_output_info
                error_msg = f"**Research topic blocked**: {guardrail_info.get('reason', 'Topic is inappropriate')}\n\n**Category**: {guardrail_info.get('category', 'Unknown')}\n\nPlease provide a different research topic that is appropriate..."
                print(f"Input guardrail blocked: {guardrail_info.get('reason')}")
                yield error_msg
                return

            print("Topic approved. Starting research...")
            yield "Topic approved. Starting research..."
            yield "Searches planned, starting to search..."
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Research complete"
            print(f"{report.guard_rail_output} - {report.guard_rail_failed}")
            if bool(report.guard_rail_failed):
                yield f"Guard rail {report.guard_rail_output} - {report.guard_rail_failed} "
            else:
                yield f"Guard rail {report.guard_rail_output} \n{report.markdown_report}"
        

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
        try:
            result = await Runner.run(
                writer_agent,
                input,
            )

        except OutputGuardrailTripwireTriggered:
            print("Output guardrail tripped")
            return result.final_output_as(ReportData)

        print("Finished writing report")
        print(result.final_output_as(ReportData).guard_rail_output)
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
        return report
    
    async def generate_clarifying_questions(self, query: str) -> str:
        """ Generate clarification questions based on the user's research topic """
        print("Generating clarification questions...")
        input = f"Analyze this research query and generate 3 clarifying questions that would help refine the research: {query}"

        try: 
            questions = await Runner.run(
                clarifying_agent,
                input
            )
            print("Generated clarification questions")
            return questions.final_output
        except InputGuardrailTripwireTriggered as e:
            # Input guardrail blocked the research topic
            guardrail_info = e.guardrail_output_info
            error_msg = f"**Research topic blocked**: {guardrail_info.get('reason', 'Topic is inappropriate')}\n\n**Category**: {guardrail_info.get('category', 'Unknown')}\n\nPlease provide a different research topic."
            print(f"Input guardrail blocked clarifying questions: {guardrail_info.get('reason')}")
            return error_msg
        except Exception as e:
            print(f"Error generating questions: {e}")
            return ""