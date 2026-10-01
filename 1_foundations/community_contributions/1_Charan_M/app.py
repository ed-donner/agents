import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import gradio as gr

# Load environment variables
load_dotenv(override=True)

# Pushover Setup
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

def push(message):
    print(f"Push: {message}")
    if pushover_user and pushover_token:
        payload = {"user": pushover_user, "token": pushover_token, "message": message}
        requests.post(pushover_url, data=payload)
    else:
        print("Pushover credentials not set in .env")

def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return "OK"

def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    return "OK"

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {"type": "string", "description": "Any additional info about the conversation that's worth recording to give context"}
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
            "question": {"type": "string", "description": "The question that couldn't be answered"},
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json}
]

def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name}", flush=True)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else "No tool found"
        results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
    return results

# Read Context from pdf and summary
# Assuming linkdin.pdf and summary.txt are in the same directory as app.py
try:
    reader = PdfReader("linkdin.pdf")
    linkedin = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            linkedin += text
except FileNotFoundError:
    linkedin = "LinkedIn profile not provided yet."

with open("summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

system_prompt = f"""
# Your role
You are a digital twin running on a website, chatting with visitors of the website.
You represent the person who's website you are on.
You answer questions related to their career, background, skills and experience.

Here are the details of the person you are representing:
{summary}

If asked, you explain clearly that you are an AI that is the digital twin of this person.

# Context
Here is a summary of the person's LinkedIn profile so that you can answer questions:
{linkedin}

# Rules
Engage with the user. Be professional and engaging, as if talking to a potential client or future employer who came across the website.
Only answer questions related to career, background, skills and experience.
If the user asks about something unrelated, then steer the conversation back to professional topics.

Always stay in character as the digital twin of the person you are representing. Represent the person.

If the user would like to get in touch, then ask for their email, and use your tool to record their email for follow-up.

IMPORTANT:
If you don't know the answer, use your tool to record the question, and then tell the user that you don't know. Never make up an answer.
"""

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
if openrouter_api_key:
    # Use OpenRouter if the key is provided
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_api_key)
    MODEL_NAME = "openai/gpt-4o-mini"
else:
    # Fallback to OpenAI directly
    client = OpenAI()
    MODEL_NAME = "gpt-4o-mini"

def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}]
    
    # Process history correctly regardless of Gradio version passing tuples or dicts
    for item in history:
        if isinstance(item, dict):
            messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        else:
            messages.append({"role": "user", "content": item[0]})
            messages.append({"role": "assistant", "content": item[1]})
            
    messages.append({"role": "user", "content": message})
    
    response = client.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    
    while response.choices[0].finish_reason == "tool_calls":
        resp_msg = response.choices[0].message
        tool_calls = resp_msg.tool_calls
        results = handle_tool_calls(tool_calls)
        messages.append(resp_msg)
        messages.extend(results)
        response = client.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
        
    return response.choices[0].message.content

if __name__ == "__main__":
    gr.ChatInterface(chat).launch(inbrowser=True)
