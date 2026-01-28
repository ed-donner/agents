""" 
    Because the agent has been provided with the general information tool, 
    the result of this program should be the university address.

    The provided prompts and instructions for this system
    should work, and should result in the university address,
    phone number and email address being returned when requested
    by the user. If the agent does not return this information,
    perhaps because a weaker model is used by this agent, then you
    might need to tweak the instructions and / or the tool_description
    in order to give the agent more guidance. That is part of the art
    of prompt engineering, this is not programming, it is data science!
"""

import asyncio
from agents import Agent, Runner
from .tools.general_information_agent import GeneralInformationAgent

class CustomerSupportAgent:
    def __init__(self):
        general_information_agent = GeneralInformationAgent()

        self.agent = Agent(
            name="Customer Support Agent",
            instructions=(
                "You are a helpful support agent offering information on Gravizot University."
                "You should only return information using tools that have been provided to you."
                "If you cannot get the requested information from a tool, you should respond with: "
                "'I do not have access to information to answer your question'"
            ),
            model="gpt-4o-mini",
            tools=[general_information_agent.agent_tool]
        )

    async def run_task(self, message: str):
        result = await Runner.run(self.agent, message)
        return result.final_output
