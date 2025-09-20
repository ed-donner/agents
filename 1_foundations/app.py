import warnings
warnings.filterwarnings("ignore")

import logging
logging.getLogger("PyPDF2").setLevel(logging.ERROR)
logging.getLogger("pypdf").setLevel(logging.ERROR)

from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr


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


class Me:

    def __init__(self):
        # Debug: Print all environment variables (without values for security)
        print("Available environment variables:")
        for key in os.environ.keys():
            if 'API' in key or 'KEY' in key:
                print(f"  {key}: {'*' * 10}")  # Hide the actual value
            else:
                print(f"  {key}: {os.environ[key]}")
        
        # Get API key from environment - handle HuggingFace secret format
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Try alternative format from HuggingFace secrets
            openai_env = os.getenv("OpenAI")
            if openai_env and openai_env.startswith("OPENAI_API_KEY="):
                api_key = openai_env.replace("OPENAI_API_KEY=", "")
            else:
                raise ValueError("OPENAI_API_KEY environment variable is not set. Please add it to your HuggingFace Space secrets.")
        
        self.openai = OpenAI(api_key=api_key)
        self.name = "Jack Agnew"
        reader = PdfReader("me/JackAgnewResume2025.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        
        # Read theatre resume
        theatre_reader = PdfReader("me/Jack Musical Theatre Resume.pdf")
        self.theatre_resume = ""
        for page in theatre_reader.pages:
            text = page.extract_text()
            if text:
                self.theatre_resume += text
                
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
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n## Theatre Resume:\n{self.theatre_resume}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
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
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()
    with gr.Blocks() as demo:
        gr.Markdown("<h2>Chat with virtual Jack!</h2>")
        chatbot = gr.Chatbot(
            avatar="ChatWithJack.jpeg",  # Make sure this file is in the same directory
            bubble_full_width=False,
            show_label=True,
            label="Jack"
        )
        msg = gr.Textbox(label="Your message")
        clear = gr.Button("Clear chat")

        def respond(user_message, chat_history):
            # Convert chat_history to OpenAI format
            formatted_history = []
            for user, bot in chat_history or []:
                if user:
                    formatted_history.append({"role": "user", "content": user})
                if bot:
                    formatted_history.append({"role": "assistant", "content": bot})
            bot_message = me.chat(user_message, formatted_history)
            chat_history = (chat_history or []) + [[user_message, bot_message]]
            return "", chat_history

        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        clear.click(lambda: None, None, chatbot, queue=False)

    demo.launch()
    