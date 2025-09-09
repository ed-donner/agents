from agents import Runner, trace, gen_trace_id, output_guardrail, GuardrailFunctionOutput, OutputGuardrailTripwireTriggered, RunContextWrapper
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from refinement_agent import refinement_agent
import asyncio

class ResearchManager:

    async def do_research(self, query: str):
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
 #           yield "Report written, sending email..."
 #           await self.send_email(report)
            yield "Research complete"
            print(f"{report.guard_rail_output} - {report.guard_rail_tripped}")
            if bool(report.guard_rail_tripped):
                yield f"Guard rail {report.guard_rail_output} - {report.guard_rail_tripped} "
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


    async def generate_refinement_questions(self, query: str) -> str:
        """ Generate clarification questions based on the user's query """
        print("Generating clarification questions...")
        input = f"Please analyze this research query and generate 3 clarifying questions that would help focus the research: {query}"
        try: 
            questions = await Runner.run(
                refinement_agent, 
                input
            )
            print("Generated clarification questions")
            return questions.final_output
        except Exception as e:
            print(f"Error generating questions: {e}")
            return ""