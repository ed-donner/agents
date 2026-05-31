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