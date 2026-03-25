"""
This file modifies and builds upon the app.py shared in the foundations folder
"""

from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import gradio as gr


load_dotenv(override=True)


INFO_USER_NAME = "Amit Bhatt"
DATA_DIR = "data"

# Move to text files for simplicity
LINKEDIN_FILE = os.path.join(DATA_DIR, "linkedin.txt")
SUMMARY_FILE = os.path.join(DATA_DIR, "summary.txt")


OPENROUTER_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# Helper functions to push notifications to Pushover
def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_business_proposal(business_proposal: str, email: str):
    push(f"Recording business proposal from {email} for {business_proposal} to follow up")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

# Tools
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_business_proposal_json = {
    "name": "record_business_proposal",
    "description": "Use this tool to record that a user is interested in a business proposal",
    "parameters": {
        "type": "object",
        "properties": {
            "business_proposal": {
                "type": "string",
                "description": "The business proposal that the user is interested in"
            },
            "email": {
                "type": "string",
                "description": "The email address of the user"
            }
        },
        "required": ["business_proposal", "email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_business_proposal_json},
    {"type": "function", "function": record_unknown_question_json}
]


class ProfessionalProfileAgent:
    """
    A class to represent a professional profile agent that can answer questions about the user's professional profile.
    """
    def __init__(self, name: Optional[str] = None, linkedin_file: Optional[str] = None, summary_file: Optional[str] = None):
        self.client = OpenAI(
            base_url=OPENROUTER_URL,
            api_key=OPENROUTER_API_KEY,
        )
        self.name = name or INFO_USER_NAME
        with open(linkedin_file or LINKEDIN_FILE, "r", encoding="utf-8") as reader:
            self.linkedin = reader.read()
        with open(summary_file or SUMMARY_FILE, "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_call(self, tool_calls):
        """
        Handle tool calls from the user.
        Args:
            tool_calls: List of tool calls from the user.
        Returns:
            List of results from the tool calls.
        """
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        """
        Generate the system prompt for the agent.
        Returns:
            System prompt for the agent.
        """
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. \
If the user is interested in a business proposal or any deals, use your record_business_proposal tool to record the business proposal and the user's email."

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        """
        Generate the messages for the agent.
        Args:
            message: The message from the user.
            history: The history of the conversation.
        Returns:
            The response from the agent.
        """
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.client.chat.completions.create(model="openai/gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content


if __name__ == "__main__":
    profile_agent = ProfessionalProfileAgent()
    gr.ChatInterface(profile_agent.chat, type="messages").launch()
