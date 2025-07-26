import asyncio
import logging
from typing import Dict, Optional

from agents import Agent, WebSearchTool, trace, Runner, gen_trace_id, function_tool
from agents.model_settings import ModelSettings

from typing import Dict
from prompts import SEARCH_AGENT_INSTRUCTIONS, PLANNER_AGENT_INSTRUCTIONS, EMAIL_AGENT_INSTRUCTIONS, WRITER_AGENT_INSTRUCTIONS
from models import WebSearchPlan, ReportData, WebSearchItem

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentManager():

    def __init__(self, model_name: str):
        self.model_name = model_name

        self.search_agent = Agent(
            name="Search agent",
            instructions=SEARCH_AGENT_INSTRUCTIONS,
            tools=[WebSearchTool(search_context_size="low")],
            model=self.model_name,
            model_settings=ModelSettings(tool_choice="required"),
        )

        self.planner_agent =  Agent(
            name="Planner Agent",
            instructions=PLANNER_AGENT_INSTRUCTIONS,
            model=self.model_name,
            output_type=WebSearchPlan,
        )

        self.email_agent = Agent(
            name="Email agent",
            instructions=EMAIL_AGENT_INSTRUCTIONS,
            tools=[AgentManager.send_email],
            model=self.model_name,
        )
        
        self.writer_agent = Agent(
            name="WriterAgent",
            instructions=WRITER_AGENT_INSTRUCTIONS,
            model=self.model_name,
            output_type=ReportData,
        )

    @staticmethod
    @function_tool
    def send_email(body: str):
        """ Write the given body to a file called 'sent_emails.txt' instead of sending an email """
        try:
            with open('sent_emails_deep_research.txt', 'a', encoding='utf-8') as f:
                f.write(body + '\n---\n')
            logger.info("Email content written to file successfully")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Failed to write email to file: {e}")
            return {"status": "error", "message": str(e)}
    
    async def plan_searches(self, query: str) -> Optional[WebSearchPlan]:
        """ Use the planner_agent to plan which searches to run for the query """
        try:
            logger.info("Planning searches...")
            result = await Runner.run(self.planner_agent, f"Query: {query}")
            search_plan = result.final_output
            logger.info(f"Will perform {len(search_plan.searches)} searches")
            return search_plan
        except Exception as e:
            logger.error(f"Failed to plan searches: {e}")
            return None

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Call search() for each item in the search plan """
        try:
            logger.info("Searching...")
            tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out failed searches
            successful_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Search {i} failed: {result}")
                else:
                    successful_results.append(result)
            
            logger.info(f"Finished searching. {len(successful_results)}/{len(results)} searches successful")
            return successful_results
        except Exception as e:
            logger.error(f"Failed to perform searches: {e}")
            return []

    async def search(self, item: WebSearchItem) -> Optional[str]:
        """ Use the search agent to run a web search for each item in the search plan """
        try:
            input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
            result = await Runner.run(self.search_agent, input_text)
            return result.final_output
        except Exception as e:
            logger.error(f"Search failed for '{item.query}': {e}")
            return None
    
    async def write_report(self, query: str, search_results: list[str]) -> Optional[ReportData]:
        """ Use the writer agent to write a report based on the search results"""
        try:
            logger.info("Thinking about report...")
            if not search_results:
                logger.warning("No search results available for report writing")
                return None
                
            input_text = f"Original query: {query}\nSummarized search results: {search_results}"
            result = await Runner.run(self.writer_agent, input_text)
            logger.info("Finished writing report")
            return result.final_output
        except Exception as e:
            logger.error(f"Failed to write report: {e}")
            return None

    async def send_email_report(self, report: ReportData) -> bool:
        """ Use the email agent to send an email with the report """
        try:
            logger.info("Writing email...")
            result = await Runner.run(self.email_agent, report.markdown_report)
            logger.info("Email sent")
            return True
        except Exception as e:
            logger.error(f"Failed to send email report: {e}")
            return False
    
    async def run(self, query: str) -> Optional[ReportData]:
        """ Run the research pipeline with comprehensive error handling """
        try:
            # Step 1: Plan searches
            search_plan = await self.plan_searches(query)
            if not search_plan:
                logger.error("Failed to create search plan")
                return None
            logger.info(f"Search plan: {search_plan}")
            
            # Step 2: Perform searches
            search_results = await self.perform_searches(search_plan)
            if not search_results:
                logger.error("No search results obtained")
                return None
            logger.info(f"Search results: {len(search_results)} items")
            
            # Step 3: Write report
            report = await self.write_report(query, search_results)
            if not report:
                logger.error("Failed to write report")
                return None
            logger.info(f"Report generated successfully")
            
            # Step 4: Send email
            email_sent = await self.send_email_report(report)
            if email_sent:
                logger.info("Hooray! Research pipeline completed successfully")
            else:
                logger.warning("Research completed but email sending failed")
            
            return report
            
        except Exception as e:
            logger.error(f"Research pipeline failed: {e}")
            return None