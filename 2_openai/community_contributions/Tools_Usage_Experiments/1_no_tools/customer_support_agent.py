""" 
    Because the agent has not been provided with any tools, 
    the result of this program will be:

    'I do not have access to information to answer your question'
"""

import asyncio
from agents import Agent, Runner

class CustomerSupportAgent:
    def __init__(self):
        self.agent = Agent(
            name="Customer Support Agent",
            instructions=(
                "You are a helpful support agent offering information on Gravizot University."
                "You should only return information using tools that have been provided to you."
                "If you cannot get the requested information from a tool, you should respond with: "
                "'I do not have access to information to answer your question'"
            ),
            model="gpt-4o-mini"
        )

    async def run_task(self, message: str):
        result = await Runner.run(self.agent, message)
        return result.final_output
