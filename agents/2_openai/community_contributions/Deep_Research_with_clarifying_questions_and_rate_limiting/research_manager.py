from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio
from typing import Optional

class ResearchManagerAgent:

    async def run(
        self,
        query: str,
        clarifying_questions: list[str],
        clarifying_answers: list[str],
        send_email_flag: bool = False,
        recipient_email: Optional[str] = None,
    ):
        """ Run the deep research process using user-provided clarification answers. """
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            yield "Planning search based on clarifications..."

            print(f"Clarifying questions: {clarifying_questions}")
            print(f"Clarifying answers: {clarifying_answers}")

            # Plan searches using clarifications and user answers
            search_plan = await self.plan_searches(query, clarifying_questions, clarifying_answers)

            yield "Searches planned, starting to search..."
            search_results = await self.perform_searches(search_plan)

            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)

            if send_email_flag and recipient_email:
                yield f"Sending report to {recipient_email}..."
                await self.send_email(report, recipient_email)
                yield "Email sent"
            else:
                yield "Skipping email step"
               
            yield "Email sent"
            yield report.markdown_report

    async def plan_searches(self, query: str, questions: list[str], answers: list[str]) -> WebSearchPlan:
        """ Plan the searches to perform based on clarifications """
        print("Planning searches...")

        # Combine clarifying Q&A into structured prompt
        clarifying_context = "\n".join(
            f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)
        )
        final_prompt = f"Query: {query}\nClarifications:\n{clarifying_context}"

        result = await Runner.run(
            planner_agent,
            input=final_prompt,
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches for the planned queries """
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

    async def search(self, item: WebSearchItem) -> Optional[str]:
        """ Perform a single web search """
        input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input_text,
            )
            return str(result.final_output)
        except Exception as e:
            print(f"Search failed: {e}")
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write a markdown report from search results """
        print("Thinking about report...")
        input_text = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input_text,
        )
        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData, recipient_email: str) -> None:
        """ Send the report via email """

        email_prompt = f"""Send the following report as an email.
        To: {recipient_email}
        Body (HTML):
        {report.markdown_report}
        """
        print(f"Sending email to: {recipient_email}")
        await Runner.run(email_agent, input=email_prompt)
        print("✅ Email sent")