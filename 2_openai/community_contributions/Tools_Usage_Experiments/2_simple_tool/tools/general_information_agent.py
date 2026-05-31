"""
    The provided prompts and instructions for this system
    should work, and should result in the university address,
    phone number and email address being returned when requested
    by the user. If the agent does not return this information,
    perhaps because a weaker model is used by this agent, then you
    might need to tweak the instructions and / or the tool_description
    in order to give the agent more guidance. That is part of the art
    of prompt engineering, this is not programming, it is data science!
"""

from agents import Agent

class GeneralInformationAgent:
    def __init__(self):
        self.agent = Agent(
            name="General Information Agent",
            model="gpt-4o-mini",
            instructions=(
                "You are a helpful support agent. You are able to offer "
                "general information about Gravizot University. Here is the "
                "information you are able to provide: "

                "Contact Information "
                "- main address: 123 Agentic Avenue, Cincinnati, Ohio 45202 "
                "- main phone number: (513) 123-4567 "
                "- main email address: info@gravizot-university.edu"
            )
        )

        self.agent_tool = self.agent.as_tool(
            tool_name="general_information_tool",
            tool_description="Provides general information such as contact details for Gravizot University."
    )