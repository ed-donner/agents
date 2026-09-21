from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr


load_dotenv(override=True)

def push(text):
    try:
        pushover_token = os.getenv("PUSHOVER_TOKEN")
        pushover_user = os.getenv("PUSHOVER_USER")
        
        if pushover_token and pushover_user:
            requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": pushover_token,
                    "user": pushover_user,
                    "message": text,
                }
            )
        else:
            print(f"Push notification not sent - missing credentials: {text}")
    except Exception as e:
        print(f"Error sending push notification: {e}")


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
        self.openai = OpenAI()
        self.name = "Manish Bhoge"
        
        # Initialize with fallback content
        self.linkedin = "Manish Bhoge's LinkedIn Profile"
        self.summary = ""
        
        # Try to read PDF files, but handle missing files gracefully
        try:
            reader1 = PdfReader("me/Profile.pdf")
            reader2 = PdfReader("me/Manish_Bhoge_v0.1.pdf")
            
            for reader in [reader1, reader2]:
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        self.linkedin += text
        except Exception as e:
            print(f"Warning: Could not read PDF files: {e}")
            # Add fallback content
            self.linkedin += "\n\nManish Bhoge is a software engineer and data scientist with experience in AI and machine learning."
        
        # Try to read summary file, but handle missing file gracefully
        try:
            with open("me/summary.txt", "r", encoding="utf-8") as f:
                self.summary = f.read()
        except Exception as e:
            print(f"Warning: Could not read summary.txt: {e}")
            # Add fallback content
            self.summary = "My name is Manish Bhoge. I'm an entrepreneur, software engineer and data scientist."


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
You are given a summary of {self.name}'s background, Profile, and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        try:
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
        except Exception as e:
            print(f"Error in chat: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Please try again later."
    

# Create the Gradio interface for Hugging Face Spaces
me = Me()
demo = gr.ChatInterface(me.chat, type="messages")

if __name__ == "__main__":
    demo.launch()
    