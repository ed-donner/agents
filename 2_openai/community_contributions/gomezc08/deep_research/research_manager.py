"""
Research Manager.
This agent organizes the entire research pipeline.
"""

instructions = """You are a professional researcher designed to answer a user's query with a report
## Steps
Follow these steps carefully...
1. **Generate Web Search Queries:** Using the web search tool, you will take the user's query and create a few web 
search queries that another agent will use.
2. **Generate a Report:** Using the reporter tool you will perform web searchs using the queries provided to create
a report for the user that answers their original query
3. **Handoff:** Handoff the generated report to the messenger agent (DO NOT PERFORM ANYTHING ELSE AFTERWARDS)

Output confirmation that the message was sent followed by the final report
"""

from agents import Agent
from messenger_agent import MessengerAgent
from report_generator_agent import ReportGeneratorAgent
from web_search_agent import WebSearchAgent

class ResearchManager:
    def __init__(self):
        self.researcher = None
        self.messenger_agent = MessengerAgent()
        self.report_generator_agent = ReportGeneratorAgent()
        self.web_search_query_agent = WebSearchAgent()
        self.tools = []
        self.handoffs = []
    
    def build_tools(self):
        # report_agent.
        if self.report_generator_agent.get_report_agent() is None:
            self.report_generator_agent.create_report_agent()

        # web search agent.
        if self.web_search_query_agent.get_web_agent() is None:
            self.web_search_query_agent.create_web_agent()
        
        # build tools.
        report_tool = self.report_generator_agent.get_report_agent().as_tool(
            tool_name="report_tool",
            tool_description="Uses the provided web search queries to generate a short report to answer user's query"
        )

        web_search_tool = self.web_search_query_agent.get_web_agent().as_tool(
            tool_name="web_search_tool",
            tool_description="To turn a user's query into multiple search queries"
        )
        
        self.tools.append(report_tool)
        self.tools.append(web_search_tool)

    def build_handoffs(self):
        # build agent if we haven't done so already.
        if self.messenger_agent.get_messenger_agent() is None:
            self.messenger_agent.create_messenger_agent()
            
        self.handoffs.append(self.messenger_agent.get_messenger_agent())
    
    def create_researcher(self):
        # checks.
        if len(self.tools) == 0:
            self.build_tools()

        if len(self.handoffs) == 0:
            self.build_handoffs()

        self.researcher = Agent(
            name="Researcher",
            instructions=instructions,
            model="gpt-4o-mini",
            tools = self.tools,
            handoffs = self.handoffs
        )