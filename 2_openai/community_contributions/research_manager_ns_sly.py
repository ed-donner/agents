"""
I implemented the same Deep Research with the use of tools to call Agents, allowing the  Research Manager to manage all  Agents through the use of tools. 
I made this architectural decision to save costs
"""

from agents import Agent, Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent
from writer_agent import writer_agent
from email_agent import email_agent

class ResearchManager:

    async def run(self, query: str):
        instructions = """
        You are a research manager on this research. Your goal is to perform a deep research on the 
        query using planner_agent_tool, search_agent_tool,writer_agent_tool and email_agent_tool.
 
        Follow these steps carefully:
        1. generate a list of search queries and reasons based on the user's research query using the planner_agent_tool.
        
        2. Search the web for the search queries using the search_agent_tool.

        3. write the search results into a detailed markdown report using the writer_agent_tool.
        
        4. Send the report to the user using the email_agent_tool.
        
        Crucial Rules:
        - You must use the tools for this task — do not write them yourself.
        - Ensure each step builds on the previous one and maintains focus on the original query.
        """
        planner_agent_tool = planner_agent.as_tool(tool_name="plan_searches", 
                            tool_description="Generates a list of search queries and reasons based on the user's research query."
                    )


        search_agent_tool = search_agent.as_tool(tool_name="search", 
                    tool_description="Search the web for a specific term."
                    )

        writer_agent_tool = writer_agent.as_tool(tool_name="write_report", 
        tool_description="Write search results into a detailed markdown report.")

        email_agent_tool = email_agent.as_tool(tool_name="send_email", 
        tool_description="Send an email with the report")
        tools = [
            planner_agent_tool,
            search_agent_tool,
            writer_agent_tool,
            email_agent_tool
        ]
        agent = Agent(
                    name="Research Manager",
                    instructions=instructions,
                    tools=tools)
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            result = await Runner.run(agent, query)
            yield result.final_output 


    