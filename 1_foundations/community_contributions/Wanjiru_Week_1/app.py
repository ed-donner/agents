import os
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import gradio as gr

# Load env
load_dotenv(override=True)

openai = OpenAI()

# Keys
openai_key = os.getenv("OPENAI_API_KEY")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")

# Load LinkedIn
reader = PdfReader("linkedin.pdf")
linkedin = ""

for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

summary = (
    "Software engineer with experience in building web applications using JavaScript and Python.\n\n"
    "Skilled in frontend development (React, HTML, CSS) and backend systems (Node.js, APIs, databases).\n\n"
    "Interested in AI, building scalable systems, and creating practical solutions to real-world problems.\n\n"
    "Has worked on projects involving authentication systems, APIs, and full-stack applications.\n\n"
    "Open to opportunities and collaborations in software engineering and AI-related roles."
)

name = "Wanjiru"

# System prompt
system_prompt = f"""
You are acting as {name}.

You answer questions about {name}'s career, skills, and experience.

Be professional and helpful.

If you don’t know something, say so.

If the user shows interest in contacting you, encourage them to share their email.

If the user provides an email address, you MUST call the record_user_details tool.

## Summary:
{summary}

## LinkedIn:
{linkedin}
"""

# Push notification
def push(message):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "user": pushover_user,
            "token": pushover_token,
            "message": message
        }
    )

# Tool function
def record_user_details(email):
    push(f"📩 New contact: {email}")
    return {"status": "saved"}

# Tool schema
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this when the user provides their email",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string"}
        },
        "required": ["email"]
    }
}

tools = [{"type": "function", "function": record_user_details_json}]

# Handle tool calls
def handle_tool_calls(tool_calls):
    results = []

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if tool_name == "record_user_details":
            record_user_details(**arguments)

        results.append({
            "role": "tool",
            "content": json.dumps({"status": "ok"}),
            "tool_call_id": tool_call.id
        })

    return results

# Chat function
def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]

    done = False

    while not done:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )

        finish_reason = response.choices[0].finish_reason

        if finish_reason == "tool_calls":
            msg = response.choices[0].message
            tool_calls = msg.tool_calls

            results = handle_tool_calls(tool_calls)

            messages.append(msg)
            messages.extend(results)
        else:
            done = True

    return response.choices[0].message.content

# Launch UI
if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        title="Chat with Wanjiru",
        description="Ask me about my skills, experience, and projects — or share your email to get in touch.",
    ).launch()
    