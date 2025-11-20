from agents import Runner
from planner_agent import planner_agent, WebSearchPlan, WebSearchItem
from search_agent import search_agent
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio
from opentelemetry import trace
from opentelemetry import metrics
from opentelemetry._logs import get_logger_provider
import openlit
import os 

# get the global tracer, meter, and logging provider to pass to OpenLIT initialization
tracer = trace.get_tracer(__name__)
meter_provider = metrics.get_meter_provider()
meter = meter_provider.get_meter(__name__, version="1.0.0")
logger_provider = get_logger_provider()

openlit.init(tracer=tracer, meter=meter, event_logger=logger_provider)

if os.environ.get('FROM_EMAIL_ADDRESS') is None or os.environ.get('TO_EMAIL_ADDRESS') is None: 
    print("Ensure the FROM_EMAIL_ADDRESS and TO_EMAIL_ADDRESS environment variables are set")
    exit()


class DeepResearchManager:

    async def run(self):
        """ Run the deep research process """
        query = "Latest AI Agent frameworks in 2025"
        with tracer.start_as_current_span("deep-research") as current_span:
            print("Starting research...")
            search_plan = await self.plan_searches(query)
            search_results = await self.perform_searches(search_plan)
            report = await self.write_report(query, search_results)
            await self.send_email(report)  
            print("Hooray!")

    async def plan_searches(self, query: str):
        """ Use the planner_agent to plan which searches to run for the query """
        print("Planning searches...")
        result = await Runner.run(planner_agent, f"Query: {query}")
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output

    async def search(self, item: WebSearchItem):
        """ Use the search agent to run a web search for each item in the search plan """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        result = await Runner.run(search_agent, input)
        return result.final_output

    async def perform_searches(self, search_plan: WebSearchPlan):
        """ Call search() for each item in the search plan """
        print("Searching...")
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = await asyncio.gather(*tasks)
        print("Finished searching")
        return results

    async def write_report(self, query: str, search_results: list[str]):
        """ Use the writer agent to write a report based on the search results"""
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(writer_agent, input)
        print("Finished writing report")
        return result.final_output

    async def send_email(self, report: ReportData):
        """ Use the email agent to send an email with the report """
        print("Writing email...")
        result = await Runner.run(email_agent, report.markdown_report)
        print("Email sent")
        return report

def main():
   deep_research_manager = DeepResearchManager()
   asyncio.run(deep_research_manager.run())

if __name__ == "__main__":
    main()