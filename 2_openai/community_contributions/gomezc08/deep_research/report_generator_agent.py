""" Report Generator Agent
This agent is responsible for generating a report based on the original query and web searches.
"""

from agents import Agent, WebSearchTool, ModelSettings

report_instructions = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query and web searches.\n"
    "You should generate a report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 100-150 words."
)

class ReportGeneratorAgent:
    def __init__(self):
        self.report_agent = None

    def get_report_agent(self):
        return self.report_agent
    
    def create_report_agent(self):
        self.report_agent = Agent(
            name="Report Agent",
            instructions=report_instructions,
            model="gpt-4o-mini",
            tools=[WebSearchTool(search_context_size='low')],
            model_settings=ModelSettings(tool_choice='required')
        )