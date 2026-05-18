from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel, Field
import http.client, urllib


load_dotenv(override=True)



def push(text):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": os.getenv("PUSHOVER_TOKEN"),
        "user": os.getenv("PUSHOVER_USER_KEY"),
        "message": text,
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

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
                "description": "The email address of this user",
                "type": "string"
            },
            "name": {
                "description": "The user's name, if they provided it",
                "type": "string"
            },
            "notes": {
                "description": "Any additional information about the conversation that's worth recording to give context",
                "type": "string"
            }
        },
        "additionalProperties": "False",
        "required": ["email"]
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
        "additionalProperties": "False"
    }
}



tools = [{"type": "function", "function": record_user_details_json}, {"type": "function", "function": record_unknown_question_json}]



class Me:
    def __init__(self):
        self.name = "Ed Donner"
        self.llm = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
        self.linkedin = ""
        reader = PdfReader("me/linkedin.pdf")

        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_calls(self, tool_calls):
        tool_messages = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**args) if tool else {}
            tool_messages.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return tool_messages

    
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


    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + [{"role": h["role"], "content": h["content"]} for h in history] + [{"role": "user", "content": message}]

        done = False
        while not done:
            res = self.llm.chat.completions.create(model="qwen/qwen3.5-9b", messages=messages, tools=tools)

            if res.choices[0].finish_reason == "tool_calls":
                message = res.choices[0].message
                tool_calls = message.tool_calls
                result = self.handle_tool_calls(tool_calls)
                messages.append(message)
                messages.extend(result)
            else:
                done = True

        return res.choices[0].message.content




if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat).launch()
