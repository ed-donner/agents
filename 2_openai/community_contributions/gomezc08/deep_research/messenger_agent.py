"""
Messenger Agent.
This agent is responsible for crafting a message to the user about the research. 
"""

import os
import requests
from agents import Agent, function_tool, ModelSettings

MESSENGER_INSTRUCTIONS = """
Craft a short message to the user that uses the following...
- 1-2 sentence message introduction
- Generated report from the Report Agent (DO NOT MAKE UP ANYTHING HERE)
Then send the message using your tools.
Output an acknowledgement that the message has been sent as well as the final output from the Report Agent  
"""

class MessengerAgent:
    def __init__(self):
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        self.pushover_url = "https://api.pushover.net/1/messages.json"
        self.message_agent = None

    def _create_send_message_tool(self):
        """Create the send_message tool with access to instance variables"""
        pushover_user = self.pushover_user
        pushover_token = self.pushover_token
        pushover_url = self.pushover_url
        
        @function_tool
        def send_message(message: str) -> str:
            """Send a message via Pushover"""
            payload = {"user": pushover_user, "token": pushover_token, "message": message}
            response = requests.post(pushover_url, data=payload)
            return f"Message sent successfully with status code: {response.status_code}"
        
        return send_message
    
    def get_messenger_agent(self):
        return self.message_agent
    
    def create_messenger_agent(self):
        self.message_agent = Agent(
            name="Messenger Agent",
            instructions=MESSENGER_INSTRUCTIONS,
            model="gpt-4o-mini",
            tools=[self._create_send_message_tool()],
            model_settings=ModelSettings(tool_choice='required')
        )