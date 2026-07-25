from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from telemetry_utils import traced_llm_call
from opentelemetry import trace as otel_trace
import asyncio

# Use the tracer you configured in your main file
tracer = otel_trace.get_tracer("research")


class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            with tracer.start_as_current_span("research.run") as span:
                span.set_attribute("query", query)
                print("Starting research...")
                
                search_plan = await self.plan_searches(query)
                yield "Searches planned, starting to search..."     
                
                search_results = await self.perform_searches(search_plan)
                yield "Searches complete, writing report..."

                report = await self.write_report(query, search_results)
                yield "Report written, sending email..."

                await self.send_email(report)
                yield "Email sent, research complete"
                
                yield report.markdown_report
        

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")

        #result = await Runner.run(
        #    planner_agent,
        #    f"Query: {query}",
        #)
        with tracer.start_as_current_span("research.plan_searches"):
            prompt = f"Query: {query}"

            result = await traced_llm_call(
                model="gpt-4.1",
                prompt=prompt,
                call_fn=lambda: Runner.run(planner_agent, prompt)
            )
            print(f"Will perform {len(result.final_output.searches)} searches")
            return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        #tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        #results = []
        #for task in asyncio.as_completed(tasks):
        #    result = await task
        #    if result is not None:
        #        results.append(result)
        #    num_completed += 1
        #    print(f"Searching... {num_completed}/{len(tasks)} completed")
        #print("Finished searching")
        #return results
        with tracer.start_as_current_span("research.perform_searches"):
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
        #input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        #try:
        #    result = await Runner.run(
        #        search_agent,
        #        input,
        #    )
        #    return str(result.final_output)
        #except Exception:
        #    return None
        with tracer.start_as_current_span("research.search") as span:
            span.set_attribute("search.query", item.query)
            span.set_attribute("search.reason", item.reason)

            input = f"Search term: {item.query}\nReason for searching: {item.reason}"

            try:
                result = await traced_llm_call(
                    model="gpt-4.1",
                    prompt=input,
                    call_fn=lambda: Runner.run(search_agent, input)
                )
                return str(result.final_output)

            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        #input = f"Original query: {query}\nSummarized search results: {search_results}"
        #result = await Runner.run(
        #    writer_agent,
        #    input,
        #)

        #print("Finished writing report")
        #return result.final_output_as(ReportData)
        with tracer.start_as_current_span("research.write_report"):
            input = f"Original query: {query}\nSummarized search results: {search_results}"

            result = await traced_llm_call(
                model="gpt-4.1",
                prompt=input,
                call_fn=lambda: Runner.run(writer_agent, input)
            )
            print("Finished writing report")
            return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        #result = await Runner.run(
        #    email_agent,
        #    report.markdown_report,
        #)
        #print("Email sent")
        #return report
        with tracer.start_as_current_span("research.send_email"):
            input = report.markdown_report

            await traced_llm_call(
                model="gpt-4.1",
                prompt=input,
                call_fn=lambda: Runner.run(email_agent, input)
            )
            print("Email sent")
            return report
