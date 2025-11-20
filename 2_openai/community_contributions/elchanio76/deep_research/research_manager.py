from agents import Runner, trace, gen_trace_id, Usage
from search_agent import search_agent
from planner_agent import PlannerAgent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from qa_agent import qa_agent
import asyncio

class ResearchManager:
    def __init__(self):
        self.report: ReportData | None = None
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.cost: float = 0.0

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            search_plan = await self.plan_searches(query, model="gpt-4o-mini", num_searches=5)
            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            self.report = report # Store the report

            yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report
        
    async def chat(self, message: str, history: list[tuple[str, str]]):
        """ Run the chat Q & A process for the generated report """
        if self.report is None:
            yield "No report available. Please run a research query first."
            return
        
        trace_id = gen_trace_id()
        # Only include report if this is the first message in the conversation
        if not history:
            message = f"##Question: {message}\n##Report:\n{self.report.markdown_report}"
        else:
            message = f"##Question: {message}\n##Context: {history}"
        with trace("Chat trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting chat...")
            result = await Runner.run(
                qa_agent,
                message,
            )
            yield result.final_output.answer

    def update_usage_stats(self, usage:Usage)->None:
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        input_token_cost = 0.15/1000000
        output_token_cost = 0.60/1000000
        self.cost += usage.input_tokens*input_token_cost + usage.output_tokens*output_token_cost

    async def plan_searches(self, query: str, model:str="gpt-4o-mini", num_searches: int = 5) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        planner_agent = PlannerAgent(model=model, num_searches=num_searches)
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        self.update_usage_stats(result.context_wrapper.usage)
        print(f"Total cost: {self.cost}")
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
        
        print(f"Total cost: {self.cost}")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            self.update_usage_stats(result.context_wrapper.usage)
            # Add the search tool cost to the total cost
            # TODO: Find out if there's a more elegant way to do this
            self.cost += 25/1000
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
        self.update_usage_stats(result.context_wrapper.usage)
        print("Finished writing report")
        print(f"Total cost: {self.cost}")
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        self.update_usage_stats(result.context_wrapper.usage)
        print("Email sent")
        print(f"Total cost: {self.cost}")
        return report