from agents import Runner, trace, gen_trace_id, Agent
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from evaluator_agent import evaluator_agent
import asyncio

MAX_EVALUATION_ITERATIONS = 2
class ResearchManager:

    async def run(self, query: str):
        planner_agent_tool_description = "Generate a set of web searches to best answer a query"
        planner_agent_tool = planner_agent.as_tool(tool_name="Planner_Agent", tool_description=planner_agent_tool_description)

        search_agent_tool_description = "Perform searches based on a search term"
        search_agent_tool = search_agent.as_tool(tool_name="Search_Agent", tool_description=search_agent_tool_description)

        writer_agent_tool_description = "Given a research query and a summary of search results, write a cohesive report for the research query"
        writer_agent_tool = writer_agent.as_tool(tool_name="Writer_Agent", tool_description=writer_agent_tool_description)

        email_agent_tool_description = "Send email of generated report"
        email_agent_tool = email_agent.as_tool(tool_name="Email_Agent", tool_description=email_agent_tool_description)

        evaluator_agent_tool_description = """Evaluate the quality of the research report"""
        evaluator_agent_tool = evaluator_agent.as_tool(tool_name="Evaluator_Agent", tool_description=evaluator_agent_tool_description)

        research_tools = [planner_agent_tool, search_agent_tool, writer_agent_tool, email_agent_tool, evaluator_agent_tool]

        research_instructions = f"""You are a research assistant. Your job is to perform deep research to answer questions. 
        You will use the following tools to help you with your research: Planner_Agent, Search_Agent, Writer_Agent, Evaluator_Agent, and Email_Agent. 
        You should first use the Planner_Agent to generate a set of web searches to best answer the query. 
        Then, you should use the Search_Agent to perform the searches you planned. 
        After you have completed your searches, you should use the Writer_Agent to write a cohesive final report for the research query.
        After writing the final report, you must use the evaluator agent to evaluate the quality of the report.
        If the report is approved by the evaluator, you should use the Email_Agent to send an email of the report, and return the report as the output of the research process.
        If the report is not approved by the evaluator, you should use the feedback and suggestions from the evaluator to improve the report by rewriting it with the Writer_Agent. 
        You should retry this process of evaluation and improvement a maximum of {MAX_EVALUATION_ITERATIONS} times.
        If after {MAX_EVALUATION_ITERATIONS} iterations the report is still not approved, you should send an email of the final version of the report, 
        even if it is not approved by the evaluator and then return the final version of the report as the output of the research process. 
        Do not return any additional content other than the final report. No fluff"""

        research_agent = Agent(
            name="Research Agent",
            instructions=research_instructions,
            tools = research_tools,
            model="gpt-4o-mini"
        )

        trace_id = gen_trace_id()
        with trace("Generate and send research report", trace_id=trace_id):
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            yield "Starting research..."
            result = await Runner.run(research_agent, query)
            yield "Research complete"
            yield result.final_output
