from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from clarifying_agent import clarifying_agent, enhance_query_agent, ClarifyingQuestions, EnhancedQuery
import asyncio

class ResearchManager:

    async def run(self, query: str, clarifying_answers: list[str] = None):
        """ Run the deep research process with optional clarifying questions workflow"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            
            # If no clarifying answers provided, ask for clarifications
            if clarifying_answers is None:
                yield "Generating clarifying questions..."
                clarifying_questions = await self.generate_clarifying_questions(query)
                yield f"Please answer these clarifying questions:\n" + "\n".join([f"{i+1}. {q}" for i, q in enumerate(clarifying_questions.questions)])
                return  # Exit early to wait for user responses
            
            # If clarifying answers provided, enhance the query
            yield "Processing your clarifications..."
            enhanced_query_data = await self.enhance_query_with_clarifications(query, clarifying_answers)
            final_query = enhanced_query_data.enhanced_query
            
            yield f"Enhanced query: {final_query}"
            yield "Starting research with enhanced query..."
            
            search_plan = await self.plan_searches(final_query)
            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(final_query, search_results)
            yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report

    async def generate_clarifying_questions(self, query: str) -> ClarifyingQuestions:
        """ Generate clarifying questions for the user """
        print("Generating clarifying questions...")
        result = await Runner.run(
            clarifying_agent,
            f"Query: {query}",
        )
        return result.final_output_as(ClarifyingQuestions)

    async def enhance_query_with_clarifications(self, original_query: str, clarifying_answers: list[str]) -> EnhancedQuery:
        """ Enhance the original query with user clarifications """
        print("Enhancing query with clarifications...")
        
        # First, get the clarifying questions that were asked
        clarifying_questions = await self.generate_clarifying_questions(original_query)
        
        # Create the input for the enhance query agent
        input_text = f"""Original Query: {original_query}

Clarifying Questions Asked:
{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(clarifying_questions.questions)])}

User Responses:
{chr(10).join([f"{i+1}. {a}" for i, a in enumerate(clarifying_answers)])}"""
        
        result = await Runner.run(
            enhance_query_agent,
            input_text,
        )
        return result.final_output_as(EnhancedQuery)

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
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
        return report