"""
Professional AI Agent for Daniel Marulanda

This project creates an intelligent agent that answers professionally about Daniel Marulanda 
based on his CV, summary, and skills data. The agent implements an Evaluator pattern 
to ensure response quality.

Architecture:
- Main Agent (Me class): Uses Ollama (Local llama3.2) to generate professional responses
- Skills Tool: Retrieves Daniel's technical skills and experience levels
- Evaluator Agent: Uses OpenAI GPT-4o-mini to review and validate responses
- Quality Control: Implements retry mechanism when responses don't meet standards

The agent is designed to represent Daniel on his website, engaging with potential 
clients or employers in a professional manner while maintaining accuracy about his 
background and expertise.
"""

from dotenv import load_dotenv
from openai import OpenAI
import json
import os
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel




load_dotenv(override=True)

def record_user_details(email, name="Name not provided", notes="not provided"):
    print(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    print(f"Recording {question}")
    return {"recorded": "ok"}

def get_profile_skills():
    ## TODO: Implement this method to return the skills from the LinkedIn profile using its API
    print("Getting profile skills")
    return {"skills": [
        {"skill": "JavaScript", "yearsOfExperience": 7},
        {"skill": "Angular", "yearsOfExperience": 7},
        {"skill": "TypeScript", "yearsOfExperience": 7},
        {"skill": "React", "yearsOfExperience": 5},
        {"skill": "Java", "yearsOfExperience": 5},
        {"skill": "Spring Boot", "yearsOfExperience": 5},
        {"skill": "Docker", "yearsOfExperience": 5},
        {"skill": "AWS", "yearsOfExperience": 5},
        {"skill": "AI Agents", "yearsOfExperience": 1}
    ]}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "strict": True,
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
        "required": ["email", "name", "notes"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "strict": True,
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

get_profile_skills_json = {
    "name": "get_profile_skills",
    "description": "Get the skills from the profile",
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json},
        {"type": "function", "function": get_profile_skills_json}]

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

class Evaluator:
    def __init__(self, name="Daniel Marulanda"):
        self.ollama = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.model = "llama3.2"
        self.name = name
        reader = PdfReader("me/daniel-cv.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/daniel-summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        self.evaluator_system_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
        You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
        The Agent is playing the role of {self.name} and is representing {self.name} on their website. \
        The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        The Agent has been provided with context on {self.name} in the form of their summary and LinkedIn details. Here's the information:"

        self.evaluator_system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        self.evaluator_system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."

    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
        user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return user_prompt
        
    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def evaluate(self, reply, message, history) -> Evaluation:
        messages = [{"role": "system", "content": self.evaluator_system_prompt}] + [{"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}]
        done = False
        while not done:
            response = self.ollama.chat.completions.parse(model=self.model, messages=messages, tools=tools, response_format=Evaluation)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.parsed


class Me:
    def __init__(self, name="Daniel Marulanda"):
        self.openai = OpenAI()
        self.name = name
        reader = PdfReader("me/daniel-cv.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/daniel-summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_call(self, tool_calls):
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
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
        particularly questions related to {self.name}'s career, background, skills and experience. \
        Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
        You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
        Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def rerun(self, reply, message, history, feedback):
        updated_system_prompt = self.system_prompt() + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
        response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content
    
    def chat(self, message, history):
        evaluator = Evaluator()
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        reply = response.choices[0].message.content

        
        evaluation = evaluator.evaluate(reply, message, history)
        if evaluation.is_acceptable:
            print("Passed evaluation - returning reply")
        else:
            print("Failed evaluation - retrying")
            print(evaluation.feedback)
            reply = self.rerun(reply, message, history, evaluation.feedback)       
        return reply
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    