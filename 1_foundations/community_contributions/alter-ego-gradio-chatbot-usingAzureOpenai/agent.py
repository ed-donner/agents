from openai import AzureOpenAI
from dotenv import load_dotenv
import os
from tools import handle_tool_calls, TOOLS
from prompt import build_system_prompt

load_dotenv()


class ConversationAgent:
    def __init__(self, name="Harsh Patel"):
        """Initialize the agent with Azure OpenAI client and system prompt."""
        self.client = AzureOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT")
        )
        self.name = name
        self.system_prompt = build_system_prompt(name)
        
    def chat(self, message, history):
        messages = (
            [{"role": "system", "content": self.system_prompt}]
            + history
            + [{"role": "user", "content": message}]
        )
        
        done = False
        while not done:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS
            )
            
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == "tool_calls":
                message_with_tool_calls = response.choices[0].message
                tool_calls = message_with_tool_calls.tool_calls
                tool_results = handle_tool_calls(tool_calls)
                
                messages.append(message_with_tool_calls)
                messages.extend(tool_results)
            else:
                done = True
                
        return response.choices[0].message.content
