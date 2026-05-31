from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from guardrails import RateLimitGuard
from clarifying_questions import ClarifyingQuestionsTool
import asyncio
import logging
from typing import AsyncGenerator, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResearchManager:
    """Manages the end-to-end deep research process"""
    
    def __init__(self):
        self.rate_limiter = RateLimitGuard(max_queries_per_hour=10)

    async def run(
        self, 
        query: str, 
        skip_clarifying: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Run the deep research process
        
        Args:
            query: Research query from user
            skip_clarifying: If True, skip clarifying questions
            
        Yields:
            Status updates and final report
        """
        try:
            # Check rate limits
            can_proceed, rate_limit_msg = self.rate_limiter.can_process_query()
            if not can_proceed:
                yield f"⏱️ **Rate Limit**: {rate_limit_msg}"
                return
            
            logger.info(f"Processing query: {query[:100]}...")
            
            # Generate trace ID
            trace_id = gen_trace_id()
            
            with trace("Research trace", trace_id=trace_id):
                yield f"🔍 **Starting Deep Research**\n"
                yield f"📊 View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n\n"
                
                # Step 1: Planning (guardrails applied by agent)
                logger.info("Planning searches...")
                yield "**Step 1/4**: Planning searches...\n"
                search_plan = await self.plan_searches(query)
                yield f"✅ Planned {len(search_plan.searches)} searches\n\n"
                
                # Step 2: Searching (guardrails applied by agent)
                logger.info("Performing searches...")
                yield "**Step 2/4**: Performing web searches...\n"
                search_results = await self.perform_searches(search_plan)
                
                if not search_results:
                    yield "❌ **Error**: No search results obtained"
                    return
                
                yield f"✅ Completed {len(search_results)} searches\n\n"
                
                # Step 3: Writing (guardrails applied by agent)
                logger.info("Writing report...")
                yield "**Step 3/4**: Synthesizing research and writing report...\n"
                report = await self.write_report(query, search_results)
                yield "✅ Report completed\n\n"
                
                # Step 4: Email
                logger.info("Sending email...")
                yield "**Step 4/4**: Sending email...\n"
                await self.send_email(report)
                yield "✅ Email sent\n\n"
                
                yield "---\n"
                yield "# 📝 Research Complete\n\n"
                yield report.markdown_report
                
                logger.info("Research completed successfully")
                
        except Exception as e:
            logger.error(f"Research failed: {str(e)}", exc_info=True)
            yield f"\n\n❌ **Error**: Research process failed - {str(e)}"
            yield "\n\nPlease try again with a different query or contact support if the issue persists."
        

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """
        Plan the searches to perform for the query
        
        Args:
            query: Sanitized research query
            
        Returns:
            WebSearchPlan with list of searches to perform
        """
        try:
            logger.debug("Planning searches...")
            result = await Runner.run(
                planner_agent,
                f"Query: {query}",
            )
            plan = result.final_output_as(WebSearchPlan)
            logger.info(f"Planned {len(plan.searches)} searches")
            return plan
        except Exception as e:
            logger.error(f"Search planning failed: {str(e)}")
            raise RuntimeError(f"Failed to plan searches: {str(e)}")

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """
        Perform concurrent web searches
        
        Args:
            search_plan: Plan containing searches to execute
            
        Returns:
            List of search result summaries
        """
        try:
            logger.debug(f"Starting {len(search_plan.searches)} concurrent searches...")
            num_completed = 0
            tasks = [
                asyncio.create_task(self.search(item)) 
                for item in search_plan.searches
            ]
            results = []
            
            for task in asyncio.as_completed(tasks):
                result = await task
                if result is not None:
                    results.append(result)
                num_completed += 1
                logger.debug(f"Search progress: {num_completed}/{len(tasks)} completed")
            
            logger.info(f"Completed searches: {len(results)}/{len(tasks)} successful")
            return results
            
        except Exception as e:
            logger.error(f"Search execution failed: {str(e)}")
            raise RuntimeError(f"Failed to perform searches: {str(e)}")

    async def search(self, item: WebSearchItem) -> Optional[str]:
        """
        Perform a single web search
        
        Args:
            item: WebSearchItem containing query and reason
            
        Returns:
            Search result summary or None if failed
        """
        input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input_text,
            )
            logger.debug(f"Search completed: {item.query}")
            return str(result.final_output)
        except Exception as e:
            logger.warning(f"Search failed for '{item.query}': {str(e)}")
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """
        Generate comprehensive research report
        
        Args:
            query: Original research query
            search_results: List of search result summaries
            
        Returns:
            ReportData containing report and metadata
        """
        try:
            logger.debug("Generating report...")
            input_text = (
                f"Original query: {query}\n\n"
                f"Summarized search results:\n"
                f"{chr(10).join(f'{i+1}. {result}' for i, result in enumerate(search_results))}"
            )
            
            result = await Runner.run(
                writer_agent,
                input_text,
            )
            
            report = result.final_output_as(ReportData)
            logger.info("Report generation completed")
            return report
            
        except Exception as e:
            logger.error(f"Report writing failed: {str(e)}")
            raise RuntimeError(f"Failed to write report: {str(e)}")
    
    async def send_email(self, report: ReportData) -> None:
        """
        Send research report via email
        
        Args:
            report: ReportData to send
        """
        try:
            logger.debug("Sending email...")
            await Runner.run(
                email_agent,
                report.markdown_report,
            )
            logger.info("Email sent successfully")
        except Exception as e:
            # Log but don't fail the entire process if email fails
            logger.error(f"Email sending failed: {str(e)}", exc_info=True)
            logger.info("Continuing despite email failure...")
