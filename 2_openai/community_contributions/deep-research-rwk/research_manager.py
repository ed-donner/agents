from agents import Runner, trace, gen_trace_id
#from pydantic import BaseModel, Field
from planner_agent import planner_agent, WebSearchPlan
from search_agent import search_agent, SearchResults
from filter_agent import filter_agent, FilteredResults
from writer_agent import writer_agent, ReportData
from review_agent import review_agent, ReviewResult
from email_agent import email_agent
# import asyncio
import parameters as param


# prints and yields, manages & shows progress of the project
class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""

        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("\nStarting research...")
            yield "Starting research, starting to plan searches, ..."

        # plan the searches
            # search_plan is a WebSearchPlan object (planner_agent.py)
            search_plan = await self.plan_searches(query)
            '''
            print(f"\nPerform {len(search_plan.searches)} searches:")
            for search in search_plan.searches:
                print(f"\n\t  - {search.search_term}\n\t - ({search.reason})")
            '''
            print("Searches planned, starting to search...")
            yield "Searches planned, starting to search..."

        # perform the searches
            # search_results is a SearchResults object (search_agent.py)
            search_results = await self.perform_searches(query,search_plan)
            '''
            print(f"\nUsed {len(search_results.results)} searches:")
            for search in search_results.results:
                print(search)
                print(f"\n\t  - {search.source}\n\t - ({search.summary})\n")
            '''
            print("Searches complete, starting to filter searches, ...")
            yield "Searches complete, starting to filter searches, ..."

        # filter the searches if necessary
            # filtered_output is a FilteredResults object (filter_agent.py)
            filtered_output = await self.filter_searches(query, search_results.results)
            '''
            print(f"\nUsed {len(filtered_output.results)} filteredsearches:")
            for item in filtered_output.results:
                print(item)
                print(f"\n\t  - {item.source}\n\t - ({item.summary})\n")
            '''
            print("Searches filtered, starting to write report, ...")
            yield "Searches filtered, starting to write report, ..."

        # write the report and iterate until review accepts results
            iterations = 0
            report = None
            while True:
                print(f"\nWriting draft report number {iterations+1}, ...")
                yield f"Writing draft report number {iterations+1}, ..."

        # write the draft report
                # if previous draft exists, provide this information to the writer
                if report:
                    feedback = review_result.feedback
                    previous_draft = report.markdown_report
                else:
                    feedback = []
                    previous_draft = ""
                report = await self.write_report(
                                    query, 
                                    filtered_output, 
                                    previous_draft,
                                    feedback
                )
                print(f"Draft report written, reviewing draft {iterations+1}, ...")
                yield f"Draft report written, reviewing draft {iterations+1}, ..."

        # review the draft report
                review_result = await self.review(query, 
                                                  filtered_output, 
                                                  report)
                
                if review_result.is_acceptable:
                    print(f"Review draft {iterations+1} accepted, ...")
                    yield f"Review draft {iterations+1} accepted, ..."
                    break   
                print(f"Review draft {iterations+1} not accepted, ...")
                yield f"Review draft {iterations+1} not accepted, ..."

                if iterations == param.MAX_REVIEW_ITERATIONS - 1:
                    print(f"\nMax review iterations reached, submitting draft {iterations+1} ...")
                    yield f"Max review iterations reached, submitting draft {iterations+1} ..."
                    break

                print('\nRedrafting report...')
                yield 'Redrafting report...'
                iterations += 1

            print("Report written, printing email...")
            yield "\nReport written, printing email..."
            await self.print_email(report)
            print("Email printed, research complete\n")
            yield "Email printed, research complete"
            yield report.markdown_report
        

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print("Plan completed\n")
        return result.final_output_as(WebSearchPlan)


    async def perform_searches(self, query: str, search_plan: WebSearchPlan) -> SearchResults:
        """ Perform the searches from the search plan """
        print("\nSearching...")
        input = f"Original query: {query}\nSearch items: {search_plan}"
        result = await Runner.run(
            search_agent,
            input,
        )
        print("Searches completed\n")
        return result.final_output_as(SearchResults)


    async def filter_searches(self, query: str, search_results: SearchResults) -> FilteredResults:
        """ Choose the most relevant search results for the query """
        print("\nFiltering...")
        input = f"Original query: {query}\nSearch items: {search_results}"
        result = await Runner.run(
                filter_agent,
                input,
            )
        print("Filtering completed\n")
        return result.final_output_as(FilteredResults)


    async def write_report(self, query: str, 
                           filtered_items: FilteredResults, 
                           previous_draft: str,
                           feedback: list[str]) -> ReportData:
        """ Write the report for the query """
        print("\nThinking about report...")
        input = (
            f"Original query: {query}\n "
            f"Summarized search results: {filtered_items.results}\n "
            f"Previous draft of the report: {previous_draft}"
            f"Feedback from previous review: {feedback}"
        )
        result = await Runner.run(
            writer_agent,
            input,
        )
        print("Finished writing report\n")
        return result.final_output_as(ReportData)


    async def review(self, query: str, 
                     search_results: FilteredResults, 
                     report: ReportData) -> ReviewResult:
        """ Review the report for errors and style """
        print("Reviewing report ...")
        input = ' '.join(
            [param.INSTRUCTIONS_REVIEW, 
            f"\nUser's Query: {query}",
            f"\nSearch results: {search_results}",
            f"\nReport: {report}",])
        
        result = await Runner.run(
            review_agent,
            input,
        )
        return result.final_output_as(ReviewResult)
        
    
    async def print_email(self, report: ReportData) -> None:
        print("\nWriting email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Report published\n")
        return report