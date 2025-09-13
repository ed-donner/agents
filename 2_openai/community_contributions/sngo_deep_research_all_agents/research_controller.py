from agents import Runner, trace, gen_trace_id, Agent
from search_agents import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from perform_searches_agent import perform_searches_agent
from email_agent import email_agent
import asyncio
import constants

class ResearchController:

    planner_agent_tool = planner_agent.as_tool(tool_name="SearchPlanTool", tool_description="Plan which searches to perform for a given query")

    perform_searches_tool = perform_searches_agent.as_tool(
        tool_name="BatchWebSearchTool",
        tool_description="Perform all searches in a WebSearchPlan by calling WebSearchTool for each query."
    )

    writer_agent_tool = writer_agent.as_tool(
        tool_name="ReportWriterTool",
        tool_description="Write a summarized report based on search results."
    )

    email_agent_tool = email_agent.as_tool(
        tool_name="EmailSenderTool",
        tool_description="Send the generated report via email."
    )

    CONTROLLER_INSTRUCTIONS = f"You conduct research for a given query. \n" \
    "1. Use SearchPlanTool to plan searches. \n" \
    "2. Use BatchWebSearchTool to execute all searches. \n" \
    "3. Summarize the results with ReportWriterTool. \n" \
    "4. Send the final report using EmailSenderTool."

    controller_agent = Agent(
        name="ResearchCoordinator",
        instructions=CONTROLLER_INSTRUCTIONS,
        model=constants.model,
        tools=[
            planner_agent_tool,
            perform_searches_tool,
            writer_agent_tool
            #email_agent_tool
        ]
    )

    TOOL_LABELS = {
        "SearchPlanTool": "Planning searches",
        "BatchWebSearchTool": f"Performing {constants.HOW_MANY_SEARCHES} web searches",
        "ReportWriterTool": "Writing the report",
        "EmailSenderTool": "Sending the report via email"
    }

    async def run_research_agent(self, query):
        """
        Run the research agent with streaming output
        
        Args:
            query (str): The research query
            agent: The controller agent to use
        
        Returns:
            The final output from the stream
        """

        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            stream = Runner.run_streamed(self.controller_agent, query)
            print(query)
            async for event in stream.stream_events():
                if event.type == "raw_response_event":
                    continue
                # When the agent updates, print that
                elif event.type == "agent_updated_stream_event":
                    print(f"Agent updated: {event.new_agent.name}")
                    continue
                # When items are generated, print them
                elif event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        tool_name = event.item.raw_item.name
                        print(f"\n {self.TOOL_LABELS.get(tool_name, tool_name)}")
                        yield(f"\n {self.TOOL_LABELS.get(tool_name, tool_name)}")
                        
                    elif event.item.type == "tool_call_output_item":
                        continue
                    elif event.item.type == "message_output_item":
                        continue
                    else:
                        pass  # Ignore other event types

        print("Hooray! I am done.")
        
        yield stream.final_output