from agents import Runner, trace, gen_trace_id,function_tool, OpenAIChatCompletionsModel
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from clarifying_agent import clarifying_agent, ClarifyingOutput
from orchestrator_agent import orchestrator_agent
from evaluator_agents import research_evaluator_agent, ResearchEvaluation
from search_utils import perform_searches, search, plan_searches
import asyncio



class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            print("Starting research...")
            search_plan = await plan_searches(query)
            yield "Searches planned, starting to search..."     
            search_results = await perform_searches(search_plan)
            report = await self.write_report(query, search_results)
            yield "Evaluating report..."
            report_evaluation = await self.evaluate_research(query, report.markdown_report)
            report_success = report_evaluation.is_acceptable
            rewrite_attempt = 0

            MAX_REWRITE_ATTEMPTS = 3
            while not report_success and rewrite_attempt < MAX_REWRITE_ATTEMPTS: 
                yield "Evaluation failed, rewriting report..."
                new_report = await self.orchestrate(query, search_results,report.markdown_report, report_evaluation.feedback,search_plan)
                new_report_evaluation = await self.evaluate_research(query, new_report.markdown_report)
                report_success = new_report_evaluation.is_acceptable
                report = new_report
                rewrite_attempt +=1
            if not report_success:
                yield "Max attempts reached, sending best report..."
            else: yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report
        
    async def get_question(self, query: str, history) -> str:
        """ Get the next clarifying question """
        input = f"Clarify. Query: {query}\nConversation history: {history}"
        result = await Runner.run(
            clarifying_agent,
            input,
        )
        return result.final_output_as(ClarifyingOutput)

    async def orchestrate(self,query:str, previous_search_results: list[str],report:str, feedback:str,previous_searchplan:WebSearchPlan)-> ReportData:
        """ Orchestrate rewriting and/or performing more searches """
        input=f"Decide. Query: {query}\nprevious search results:{previous_search_results}\nreport:{report}\nfeedback:{feedback}\nprevious searchplan: {previous_searchplan}"
        new_report = await Runner.run(
            orchestrator_agent,
            input,
        )
        return new_report.final_output_as(ReportData)

    async def get_refined_query(self, query: str, history) -> str:
        """ Get the refined query based on the conversation history """
        input = f"Refine. Query: {query}\nConversation history: {history}"
        result = await Runner.run(
            clarifying_agent,
            input,
        )
        return result.final_output_as(ClarifyingOutput).refined_query




    async def evaluate_research(self, refined_query: str, report: str) -> ResearchEvaluation:
        """Evaluate whether the research report adequately addresses the researched query."""
        input = f"Query: {refined_query}\n\nReport:\n{report}"
        result = await Runner.run(research_evaluator_agent, input)
        return result.final_output_as(ResearchEvaluation)

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