from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel

load_dotenv(override=True)

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

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

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

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


EVALUATION_MAX_RETRIES = 3

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Dave Njeru"
        reader = PdfReader("me/resume.pdf")
        self.resume = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:   
                self.resume += text


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
        system_prompt = f"""You are acting as {self.name}. You are answering questions on {self.name}'s website, 
particularly questions related to {self.name}'s career, background, skills and experience. 
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. 
You are given a resume of {self.name} which you can use to answer questions. 
Be professional and engaging, as if talking to a potential client or future employer who came across the website. 
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. 
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool.

## Resume:
{self.resume}


With this context, please chat with the user, always staying in character as {self.name}.
"""
        return system_prompt

    def evaluator_system_prompt(self):
        evaluator_system_prompt = f"""You are an evaluator that decides whether a response to a question is acceptable. 
You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. 
The Agent is playing the role of {self.name} and is representing {self.name} on their website. 
The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. 
The Agent has been provided with context on {self.name} in the form of their resume. Here's the information:

## Resume:
{self.resume}


With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback.
"""
        return evaluator_system_prompt
    
    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = f"""Here's the conversation between the User and the Agent:

{history}

Here's the latest message from the User:

{message}

Here's the latest response from the Agent:

{reply}

Please evaluate the response, replying with whether it is acceptable and your feedback."""
        return user_prompt
    
    def evaluate(self, reply, message, history):
        messages = [{"role": "system", "content": self.evaluator_system_prompt()}] + [{"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}]
        response = self.openai.beta.chat.completions.parse(model="gpt-4o-mini", messages=messages, response_format=Evaluation)
        return response.choices[0].message.parsed

    def rerun(self, reply, message, history, feedback):
        updated_system_prompt = self.system_prompt() + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
        response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
        return response.choices[0].message.content 
    
    def chat(self, message, history):
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
        
        retries = 0
        evaluation = self.evaluate(reply, message, history)
        while retries < EVALUATION_MAX_RETRIES and not evaluation.is_acceptable:
            retries += 1
            reply = self.rerun(reply, message, history, evaluation.feedback)
            evaluation = self.evaluate(reply, message, history)
        return reply


    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch(ssr_mode=False)
