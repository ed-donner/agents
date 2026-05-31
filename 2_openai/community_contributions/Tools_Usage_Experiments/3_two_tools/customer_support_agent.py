""" 
    Because the agent has been provided with the courses of study tool, 
    this program should be able to provide details about the computer 
    science major, and other majors offered by the university.

    You should also still be able to get information on the university 
    address, phone number and email address. 

    If the agent does not return this information, perhaps because a 
    weaker model is used by this agent, then you might need to tweak 
    the instructions and / or the tool_description in order to give 
    the agent more guidance. That is part of the art of prompt 
    engineering, this is not programming, it is data science!

    You might even need to tweak the 1_basic_tool_prompt.txt file 
    to help the system know what to do, in fact to force it to do
    what you want it to do. Often we have to use words like MUST,
    in uppercase, to get the LLM to do what we want it to do.
"""

import asyncio
from agents import Agent, Runner
from .tools.general_information_agent import GeneralInformationAgent
from .tools.courses_of_study_agent import CoursesOfStudyAgent

class CustomerSupportAgent:
    def __init__(self):
        general_information_agent = GeneralInformationAgent()
        courses_of_study_agent = CoursesOfStudyAgent()

        self.agent = Agent(
            name="Customer Support Agent",
            instructions=(
                "You are a helpful support agent offering information on Gravizot University."
                "You should only return information using tools that have been provided to you."
                "If you cannot get the requested information from a tool, you should respond with: "
                "'I do not have access to information to answer your question'"
            ),
            model="gpt-4o-mini",
            tools=[general_information_agent.agent_tool, courses_of_study_agent.agent_tool]
        )

    async def run_task(self, message: str):
        result = await Runner.run(self.agent, message)
        return result.final_output
