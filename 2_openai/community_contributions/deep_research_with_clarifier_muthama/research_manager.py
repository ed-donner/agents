import asyncio
from agents import Runner, trace, gen_trace_id
from typing import List, Tuple

from my_agents.clarifier_agent import ClarifyingQuestions, clarifier_agent
from my_agents.contextualizer_agent import ContextualizedQuery, contextualizing_agent
from my_agents.planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from my_agents.search_agent import search_agent
from my_agents.writer_agent import writer_agent, ReportData
from my_agents.email_agent import email_agent

class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            
            print("Starting research...")

            # clarifying_questions = await self.get_clarifying_questions(query)
            # yield "Clarifying questions generated, running contextualizer..."

            # contextualized_query = await self.run_contextualizer(query, clarifying_questions)
            # yield "Contextualized query generated, starting to plan searches..."

            search_plan = await self.plan_searches(query)
            yield "Searches planned, starting to search..."

            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."

            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."

            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report

    async def get_clarifying_questions(self, user_query: str) -> Tuple[str, List]:
        query = (user_query or "").strip()
        if not query or len(query) < 5 or len(query) > 100:
            raise ValueError("Query must be 5-100 characters")

        print("Accumulating clarifying questions...")

        result = await Runner.run(clarifier_agent, f"Query: {query}")
        clarifying_questions = result.final_output_as(ClarifyingQuestions).questions

        first_question = clarifying_questions[0].clarifying_question
        formatted_first = f"**Q1**: {first_question}\n\n"

        print("Clarifying questions:\n", clarifying_questions)

        return formatted_first, clarifying_questions

    async def run_contextualizer(original_query, questions_list, answers_list):
        formatted_input = f"Original User Query:\n{original_query.strip()}\n\n"
        print("Questions list:", questions_list)

        for idx, (q, a) in enumerate(zip(questions_list, answers_list), 1):
            formatted_input += (
                f"Clarifying Question {idx}:\n{q.clarifying_question.strip()}\n"
                f"Purpose of clarifying question {idx}:\n{q.question_purpose.strip()}\n"
                f"User Answer for Question {idx}:\n{a.strip()}\n\n"
            )

        result = await Runner.run(contextualizing_agent, formatted_input)

        contextualized_query = result.final_output_as(ContextualizedQuery).contextualized_query
        return contextualized_query
    
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