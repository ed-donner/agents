from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

##########################################################################################################################################################################
## added the possibility to recieve message and email using Pushover and also created another tool to record unknown questions and project inquiries and general contact.
##########################################################################################################################################################################


load_dotenv(override=True)

my_name = "Alain Veuve"

def push(text):
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_TOKEN"),
                "user": os.getenv("PUSHOVER_USER"),
                "message": text,
            },
            timeout=5,
        )
    except Exception as e:
        print(f"[push] Warning: could not send pushover notification: {e}", flush=True)


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {"type": "string", "description": "Any additional information about the conversation that's worth recording to give context"},
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
            "email": {"type": "string", "description": "The email address of the user asking the question"},
        },
        "required": ["question", "email"],
        "additionalProperties": False
    }
}

def record_unknown_question(question, email):
    # Format the string to include both the question and the email
    notification_text = f" Unanswered Question: {question}\n User Email: {email}"
    push(notification_text)
    return {"recorded": "ok"}

#def record_general_inquiry(inquiry, email):
#    # Format the notification for general/availability questions
#    notification_text = f" New Inquiry/Availability Check:\nMessage: {inquiry}\n User Email: {email}"
#    push(notification_text)
#    return {"recorded": "ok"}

def record_unknown_question(question, email):
    # This builds the message for Pushover
    notification_text = f" Unanswered Question: {question}\n User Email: {email}"
    push(notification_text)
    return {"recorded": "ok"}

def record_general_inquiry(inquiry, email):
    # This builds the message for Pushover
    notification_text = f" Project Inquiry: {inquiry}\n User Email: {email}"
    push(notification_text)
    return {"recorded": "ok"}


record_general_inquiry_json = {
    "name": "record_general_inquiry",
    "description": "Use this tool when the user asks about project availability, wants to start a project, or has a general business inquiry.",
    "parameters": {
        "type": "object",
        "properties": {
            "inquiry": {"type": "string", "description": "The user's question or message regarding the project or availability"},
            "email": {"type": "string", "description": "The user's email address"},
        },
        "required": ["inquiry", "email"],
        "additionalProperties": False
    }
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
    {"type": "function", "function": record_general_inquiry_json},
]


class Me:
    def __init__(self):
        # --- API client guard ---
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY in environment.")
        self.openai = OpenAI()  # uses OPENAI_API_KEY by default

        self.name = my_name
        self.myprofile = ""
        # --- Load profile data with guards ---
        try:
            reader = PdfReader("me/myprofile.pdf")
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    self.myprofile += text
        except Exception as e:
            print(f"[init] Warning: could not read me/myprofile.pdf: {e}", flush=True)

        try:
            with open("me/summary.txt", "r", encoding="utf-8") as f:
                self.summary = f.read()
        except Exception as e:
            print(f"[init] Warning: could not read me/summary.txt: {e}", flush=True)
            self.summary = ""

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"[tools] Called: {tool_name} | args: {arguments}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id
            })
        return results

    def system_prompt(self):
        
        system_prompt = (
            f"You are acting as {self.name}, answering questions on your website about your career and experience. "
            f"Represent {self.name} faithfully, professionally, and engagingly.\n\n"            
            f"**CRITICAL TOOL RULES:**\n"
            f"1. **Unknown Questions:** If you don't know an answer, you MUST ask for the user's email. Once they provide it, use `record_unknown_question` with both the question and email.\n"
            f"2. **Project Inquiries:** If the user asks about project availability, starting a project soon, or hiring you, you MUST ask for their email. Once provided, use `record_general_inquiry` with their inquiry and email.\n"
            f"3. **General Contact:** If a user just wants to leave their contact info or stay in touch without a specific question, use `record_user_details`.\n\n"
            f"Privacy: Only collect email for follow-up. Do not store sensitive data."
)

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.myprofile}\n\n"
        system_prompt += f"With this context, continue the conversation, always staying in character as {self.name}."
        return system_prompt

    def chat(self, message, history):
        # history from gradio(type="messages") should already be [{"role": "...", "content": "..."}]
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        while True:
            try:
                response = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.7,
                )
            except Exception as e:
                print(f"[chat] API error: {e}", flush=True)
                return "Sorry, I ran into an error calling the model. Check server logs."

            choice = response.choices[0]
            assistant_msg = choice.message

            # If the assistant wants to call tools
            if getattr(assistant_msg, "tool_calls", None):
                tool_calls = assistant_msg.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
                messages.extend(results)
                # loop to let the model see tool outputs
                continue

            # Otherwise we have a normal answer
            return assistant_msg.content


if __name__ == "__main__":
    me = Me()
    # Launch ONLY ONE interface here
    gr.ChatInterface(me.chat, type="messages", title=f"Hi, I am {my_name}'s Linkedin Profile Assistant. How can I help you today?").launch()