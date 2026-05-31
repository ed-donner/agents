from dotenv import load_dotenv
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from openai import OpenAI

load_dotenv(override=True)

openai_key = os.getenv("OPENAI_API_KEY")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

openai = OpenAI()

def push(message):
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording interest from {name} with email {email} and notes {notes}")
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

def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    return {"recorded": "ok"}

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
    {"type" : "function", "function" : record_user_details_json}, 
    {"type" : "function", "function" : record_unknown_question_json}
]

def handle_tool_calls(tools_calls):
    results = []
    for tool_call in tools_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {function_name}", flush=True)
        
        # case 1: record_user_details
        if function_name == "record_user_details":
            result = record_user_details(**arguments)
        
        # case 2: record_unknown_question
        elif function_name == "record_unknown_question":
            result = record_unknown_question(**arguments)
        
        results.append({"role" : "tool", "content" : json.dumps(result), "tool_call_id": tool_call.id})
    
    return results

reader = PdfReader("me/Profile.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

readerResume =  PdfReader("me/Resume 2026.pdf")
resume = ""
for page in readerResume.pages:
    text = page.extract_text()
    if text:
        resume += text

name = "Chris Gomez"
 
system_prompt = f"You are acting as {name}. You are answering questions on {name}'s website, \
particularly questions related to {name}'s career, background, skills and experience. \
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

system_prompt += f"\n\n## Resume: \n {resume}\n ## LinkedIn Profile:\n{linkedin}\n\n"
system_prompt += f"With this context, please chat with the user, always staying in character as {name}."

def chat(message, history):
    # create message.
    messages = [{"role" : "system", "content" : system_prompt}] + history + [{"role" : "user", "content" : message}]
    
    isDone = False
    while isDone == False:
        # call llm.
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
            tools=tools
        )
        finish_reason = response.choices[0].finish_reason
        
        if finish_reason == "tool_calls":
            message = response.choices[0].message
            tool_calls = message.tool_calls
            results = handle_tool_calls(tool_calls)
            messages.append(message)
            messages.extend(results)
        else:
            isDone = True
    
    return response.choices[0].message.content


gr.ChatInterface(chat, type="messages").launch()