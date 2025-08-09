from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from growth_searches import growth_agent
from consensus_agent import consensus_agent
from email_agent import email_agent
from input_analyser import input_analyser, InputValidation
import asyncio
import traceback

class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print("Validating Input...")
            yield "Validating your input..."
            validation = await self.input_analyser(query)
            print("Input validation:", validation)
            if validation.valid:
                yield "Your query sounds relevant. Finalising outline for report"
                print("Starting research...")
                print("Searching growth prospects for company:", validation.company_name)
                growth_results = await self.growth_searches(validation.company_name)
                print("Growth checked, planning for metrics")
                print("Searching analyst consensus for company:", validation.company_name)
                consensus_results = await self.consensus_searches(validation.company_name)
                print("Analysed consensus, planning for metrics") 
                search_plan = await self.plan_searches(validation.company_name)
                print("Searches planned, starting to search for metrics data for company:", validation.company_name)
                yield "Finalised plan, checking critical information about the company"
                search_results = await self.perform_searches(search_plan)
                search_results.append(growth_results)
                search_results.append(consensus_results)
                yield "Completed search, writing report..."
                report = await self.write_report(query, search_results)
                yield "Report written, sending email..."
                await self.send_email(report)
                yield "Email sent, research complete, sharing report here for your reference."
                yield report.markdown_report
            else:
                yield validation.company_name

    async def input_analyser(self, query: str) -> InputValidation:
        """ Validate the input for the query"""
        print("Checking in input function..")
        result = await Runner.run(
            input_analyser,
            f"Query: {query}",
        )
        validation = result.final_output_as(InputValidation)
        return validation
    
    async def growth_searches(self, query: str) -> str | None:
        """ Perform a growth research """
        try:
            result = await Runner.run(
                growth_agent,
                f"Query: {query}",
            )
            print("search try: ",result.final_output)
            return str(result.final_output)
        except Exception as ex:
            print(f"Growth Search Exception - Type: {type(ex).__name__}")
            print(f"Growth Search Exception - Message: {str(ex)}")
            print("Full traceback:")
            traceback.print_exc()
            print("-" * 50)
            print("Growth Search Exception")
            return None

    async def consensus_searches(self, query: str) -> str | None:
        """ Perform a consensus research """
        try:
            result = await Runner.run(
                consensus_agent,
                f"Query: {query}",
            )
            print("search try: ",result.final_output)
            return str(result.final_output)
        except Exception as ex:
            print(f"Consensus Search Exception - Type: {type(ex).__name__}")
            print(f"Consensus Search Exception - Message: {str(ex)}")
            print("Full traceback:")
            traceback.print_exc()
            print("-" * 50)
            print("Consensus Search Exception")
            return None

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        print(result.final_output_as(WebSearchPlan))
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        print("Search plan searches:", search_plan.searches)
        print("Tasks: ",tasks)
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            print("Task inside for: ", task)
            print("result inside for: ", result)
            if result is not None:
                results.append(result)
                print(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        print("RESULT: ", results)
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        print("WebSearchItem : ", item)
        input_text = f"Search metric: {item.query}\nCompany name: {item.company_name}"
        print("Input Text: ",input_text)
        try:
            result = await Runner.run(
                search_agent,
                input_text,
            )
            print("search try: ",result.final_output)
            return str(result.final_output)
        except Exception as ex:
            print(f"Search Exception - Type: {type(ex).__name__}")
            print(f"Search Exception - Message: {str(ex)}")
            print("Full traceback:")
            traceback.print_exc()
            print("-" * 50)
            print("Search Exception")
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        input_text = f"Original query: {query}\nSummarized search results: {search_results}"
        print("Report Input Text",input_text)
        try:
            result = await Runner.run(
                writer_agent,
                input_text,
            )
            print("Writer try: ",result.final_output_as(ReportData))
            return result.final_output_as(ReportData)
        except Exception as ex:
            print(f"Writer Exception - Type: {type(ex).__name__}")
            print(f"Writer Exception - Message: {str(ex)}")
            print("Full traceback:")
            traceback.print_exc()
            print("-" * 50)
            print("Writer Exception")
            return None
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        print("report:", report)
        print("markdown:",report.markdown_report)
        try:
            result = await Runner.run(
                email_agent,
                report.markdown_report,
            )
            print("Emailer try: ",report)
            return report
        except Exception as ex:
            print(f"Emailer Exception - Type: {type(ex).__name__}")
            print(f"Emailer Exception - Message: {str(ex)}")
            print("Full traceback:")
            traceback.print_exc()
            print("-" * 50)
            print("Emailer Exception")
            return None
