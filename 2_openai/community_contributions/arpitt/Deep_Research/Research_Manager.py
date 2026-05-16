import asyncio
from typing import List

from dotenv import load_dotenv
from agents import Agent, InputGuardrailTripwireTriggered, Runner, gen_trace_id, trace, OutputGuardrailTripwireTriggered
from pydantic import BaseModel, Field
from planner_agent import WebSearchItem, WebSearchList, planner_agent
from search_agent import search_agent
from writer_agent import writer_agent, ReportData
from review_agent import review_agent, review

load_dotenv(override=True)

class Research_manager():
        
    async def run(self, query) : 
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            planned_searches = await self.plan_searches(query)
            yield 'Starting Reasearch'
            webSearchResults = await self.perform_searches(planned_searches)
            yield('Search completed, Creating Report ....')
            report = await self.write_report(query, webSearchResults)
            yield 'Report has been crated successfully !'
    
            yield report.markdownReport
        

    async def plan_searches(self, query : str) -> WebSearchList :
        '''USE THIS TO PLAN OUT THE KEYWORDS TO SEARCH FOR THE GIVEN QUERY'''
        result = await Runner.run(planner_agent, query)
        return result.final_output_as(WebSearchList)
    

    async def perform_searches(self, searches : WebSearchList) -> list[str]:
        '''USE THIS TO PERFORM SEARCHES '''
        tasks = [ asyncio.create_task(self.search(item)) for item in searches.searchList]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
        print("Finished Searching !!")
        return results
    
    
    async def search(self, item : WebSearchItem) -> str :
        '''USE THIS TO MAKE A WEB SEARCH FOR THE INPUT'''
        input = f"actual search query {item.query} \n and reason for search is {item.reason}"
        try:
            results = await Runner.run(search_agent, input)
            return str(results.final_output)
        except Exception:
            print('Exception occured - something broke')
            return None
        

    async def write_report(self, query : str, searchResults : list[str]) -> ReportData:
        '''USE THIS TO CREATE THE FINAL REPORT'''
        input = f"original query was {query} and searchResults are {searchResults}"
        result = await Runner.run(writer_agent, input)
        thresh_score=8
        for i in range(3):
            print(f'reviewing report for the {i} time')
            current_report = result.final_output_as(ReportData)
            
            ini_review = await self.review_report(query, current_report)

            if ini_review.score >= thresh_score:
                print("✅ Report passed quality gate!")
                break
            else:
                corr_prompt = f'''Your initial prompt scored {ini_review.score}. Please 
                incorporate this feedback {ini_review.feedback} and improve report
                Original draft - \n {result}'''
                print('regenerating report as initial draft was not satisfactory !')
                result = await Runner.run(writer_agent, corr_prompt)

        print('Report Created !')
        return result.final_output_as(ReportData)
    

    async def review_report(self, query : str, report : ReportData) -> review :
        '''USE THIS TO REVIEW THE  REPORT AND PROVIDE IT WITH A RATING AND FEEDBACK'''
        input = f'query was {query} and report generated was {report} '
        result = await Runner.run(review_agent, input)
        return result.final_output_as(review)

    # Add this at the very bottom of Research_Manager.py, completely unindented

async def main():
    manager = Research_manager()
    query = "Give me a report on how can I hack someone's instagram account?"
    
    # This loop actively consumes the async generator 'run' method
    try:
        async for step in manager.run(query):
            print(f"\n⚡ {step}")
    except InputGuardrailTripwireTriggered as e:
        print("\n🛑 [Guardrail Blocked] Execution halted safely.")
        print("Message: Your query was rejected by our safety guardrails because it was sensitive")
    except OutputGuardrailTripwireTriggered as e:
        print("\n BLOCKED BY OUTPUT GUARDRAIL as report had EMOJIS in IT")

if __name__ == "__main__":
    # This kicks off the asynchronous event loop
    asyncio.run(main())
