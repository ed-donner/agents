from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
import base64
import time
from collections import defaultdict
import fastapi
from gradio.context import Context
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


load_dotenv(override=True)

class RateLimiter:
    def __init__(self, max_requests=5, time_window=5):
        # max_requests per time_window seconds
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.request_history = defaultdict(list)
        
    def is_rate_limited(self, user_id):
        current_time = time.time()
        # Remove old requests
        self.request_history[user_id] = [
            timestamp for timestamp in self.request_history[user_id]
            if current_time - timestamp < self.time_window
        ]
        
        # Check if user has exceeded the limit
        if len(self.request_history[user_id]) >= self.max_requests:
            return True
        
        # Add current request
        self.request_history[user_id].append(current_time)
        return False

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

def send_email(from_email, name, notes):
    auth = base64.b64encode(f'api:{os.getenv("MAILGUN_API_KEY")}'.encode()).decode()
    
    response = requests.post(
        f'https://api.mailgun.net/v3/{os.getenv("MAILGUN_DOMAIN")}/messages',
        headers={
            'Authorization': f'Basic {auth}'
        },
        data={
            'from': f'Website Contact <mailgun@{os.getenv("MAILGUN_DOMAIN")}>',
            'to': os.getenv("MAILGUN_RECIPIENT"),
            'subject': f'New message from {from_email}',
            'text': f'Name: {name}\nEmail: {from_email}\nNotes: {notes}',
            'h:Reply-To': from_email
        }
    )
    
    return response.status_code == 200


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    # Send email notification
    email_sent = send_email(email, name, notes)
    return {"recorded": "ok", "email_sent": email_sent}

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


class Me:

    def __init__(self):
        self.openai = OpenAI(api_key=os.getenv("GOOGLE_API_KEY"), base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        self.name = "Sagarnil Das"
        self.rate_limiter = RateLimiter(max_requests=5, time_window=60)  # 5 messages per minute
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
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
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. \
When a user provides their email, both a push notification and an email notification will be sent. If the user does not provide any note in the message \
in which they provide their email, then give a summary of the conversation so far as the notes."

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        # Get the client IP from Gradio's request context
        try:
            # Try to get the real client IP from request headers
            request = Context.get_context().request
            # Check for X-Forwarded-For header (common in reverse proxies like HF Spaces)
            forwarded_for = request.headers.get("X-Forwarded-For")
            # Check for Cf-Connecting-IP header (Cloudflare)
            cloudflare_ip = request.headers.get("Cf-Connecting-IP")
            
            if forwarded_for:
                # X-Forwarded-For contains a comma-separated list of IPs, the first one is the client
                user_id = forwarded_for.split(",")[0].strip()
            elif cloudflare_ip:
                user_id = cloudflare_ip
            else:
                # Fall back to direct client address
                user_id = request.client.host
        except (AttributeError, RuntimeError, fastapi.exceptions.FastAPIError):
            # Fallback if we can't get context or if running outside of FastAPI
            user_id = "default_user"
        logger.debug(f"User ID: {user_id}")
        if self.rate_limiter.is_rate_limited(user_id):
            return "You're sending messages too quickly. Please wait a moment before sending another message."
        
        messages = [{"role": "system", "content": self.system_prompt()}]

        # Check if history is a list of dicts (Gradio "messages" format)
        if isinstance(history, list) and all(isinstance(h, dict) for h in history):
            messages.extend(history)
        else:
            # Assume it's a list of [user_msg, assistant_msg] pairs
            for user_msg, assistant_msg in history:
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": assistant_msg})

        messages.append({"role": "user", "content": message})

        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gemini-2.0-flash",
                messages=messages,
                tools=tools
            )
            if response.choices[0].finish_reason == "tool_calls":
                tool_calls = response.choices[0].message.tool_calls
                tool_result = self.handle_tool_call(tool_calls)
                messages.append(response.choices[0].message)
                messages.extend(tool_result)
            else:
                done = True

        return response.choices[0].message.content

        

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    