from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

load_dotenv(override=True)

def push(text):
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        print("Pushover: Missing credentials", flush=True)
        return
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": token, "user": user, "message": text},
            timeout=10
        )
        print("Pushover: Sent", flush=True)
    except Exception as e:
        print(f"Pushover: Error - {e}", flush=True)

def record_contact(email, name="Not provided", notes=""):
    message = f"Contact: {name}\nEmail: {email}\nNotes: {notes}"
    push(message)
    return {"status": "recorded"}

def record_question(question):
    push(f"Unanswered: {question}")
    return {"status": "recorded"}

tools = [
    {
        "type": "function",
        "function": {
            "name": "record_contact",
            "description": "Save contact details when someone wants to connect or needs more info",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email address"},
                    "name": {"type": "string", "description": "Name"},
                    "notes": {"type": "string", "description": "Additional notes or reason for contact"}
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_question",
            "description": "Record questions you can't answer or need clarification on",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question to record"}
                },
                "required": ["question"]
            }
        }
    }
]

def load_context():
    context = ""
    summary_path = "me/summary.txt"
    if os.path.exists(summary_path):
        with open(summary_path, "r") as f:
            context += f"Bio:\n{f.read()}\n\n"

    for file in os.listdir("me"):
        if file.endswith(".pdf"):
            reader = PdfReader(f"me/{file}")
            text = "\n".join([page.extract_text() for page in reader.pages])
            context += f"CV/Resume:\n{text}\n\n"

    return context

context = load_context()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

system_prompt = f"""You are a digital twin assistant representing this person. Use the information below to answer questions about their background, skills, and experience.

{context}

Be conversational and helpful. If someone wants to connect or you can't answer something, use the available tools."""

def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        messages.append({"role": "user", "content": h[0]})
        messages.append({"role": "assistant", "content": h[1]})
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools
    )

    while response.choices[0].message.tool_calls:
        messages.append(response.choices[0].message)
        for tool_call in response.choices[0].message.tool_calls:
            if tool_call.function.name == "record_contact":
                result = record_contact(**json.loads(tool_call.function.arguments))
            elif tool_call.function.name == "record_question":
                result = record_question(**json.loads(tool_call.function.arguments))

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools
        )

    return response.choices[0].message.content

demo = gr.ChatInterface(
    fn=chat,
    title="Digital Twin",
    description="Ask me anything about my background and experience"
)

if __name__ == "__main__":
    demo.launch()
