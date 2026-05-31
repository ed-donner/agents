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
                "You are a helpful support agent. You are able to offer "
                "detailed information about courses of study at Gravizot University."

                "You MUST NOT generate your own answers. If you are asked a quesition that "
                "you cannot answer with the data in your instructions, you MUST respond with "
                "'I do not have access to information to answer your question'."

                "You MUST NOT have markdown in the output, only text."

                "You MUST ONLY return the information provided by your instructions." 
                "You MUST NOT return any text that your instructions do not provide,"
                "such as additional descriptions or text related to the user question."

                "You MUST return the information structured in the format" 
                "provided to you. The format of the returned data MUST be in the "
                "structure provided by each tool."

                "DO NOT EVER RETURN MARKDOWN TEXT. BEFORE YOU RETURN YOUR RESPONSE, "
                "CHECK YOUR RETURN TEXT FOR MARKDOWN AND REMOVE IT"

                "DO NOT EVER RETURN MARKDOWN TEXT. BEFORE YOU RETURN YOUR RESPONSE, "
                "CHECK YOUR RETURN TEXT FOR MARKDOWN AND REMOVE IT. SO DO NOT ADD "
                "HASHMARKS OR ASTERISKS AS MARKDOWN, OR ANY OTHER MARKDOWN SYMBOLS."
                "ENSURE YOU STRIP ALL MARKDOWN FROM YOUR RESPONSE BEFORE RETURNING IT"

                "STRIP ** THAT MIGHT BE ENCLOSING TEXT AS THIS IS UNDESIRED MARKDOWN"            
            ),
            model="gpt-4o-mini",
            tools=[general_information_agent.agent_tool, courses_of_study_agent.agent_tool]
        )



    async def run_task(self, message: str):
        result = await Runner.run(self.agent, message)
        return result.final_output
