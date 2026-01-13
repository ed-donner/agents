from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import query_agent, planner_agent, FollowUpQuestions, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio

class ResearchManager:

    async def generate_questions(self, query: str) -> list[str]:
        """ Generate follow-up questions for the user to answer """
        print("Generating follow-up questions...")
        result = await Runner.run(
            query_agent,
            f"Query: {query}",
        )
        questions = result.final_output_as(FollowUpQuestions).questions
        print(f"Generated {len(questions)} questions")
        return questions

    async def run(self, query: str, questions: list[str], answers: list[str]):
        """ Run the deep research process with user's answers, yielding status updates and the final report """
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research with user answers...")
            search_plan = await self.plan_searches(query, questions, answers)
            yield "Searches planned, starting to search..."     
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report
        

    async def plan_searches(self, query: str, questions: list[str], answers: list[str]) -> WebSearchPlan:
        """ Plan the searches based on the query and user's answers """
        print("Planning searches based on user answers...")
        # Format Q&As for the planner
        qa_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)])
        input_text = f"Original Query: {query}\n\nFollow-up Questions and User's Answers:\n{qa_text}"
        
        result = await Runner.run(
            planner_agent,
            input_text,
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