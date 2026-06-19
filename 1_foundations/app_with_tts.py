from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from gtts import gTTS
import tempfile
import base64
import io

#I was planning to use elevenlabs for cloning my own voice, but it was quite expensive, so I used google TTS instead
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


def text_to_speech(text, language='en'):
    """Convert text to speech using Google TTS"""
    try:
        # Create gTTS object
        tts = gTTS(text=text, lang=language, slow=False)
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            temp_file_path = fp.name
        
        return temp_file_path
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        return None


class Me:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Lekha Satnur"
        reader = PdfReader("me/Lekha_Satnur_Resume.pdf")
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
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        # Convert history to the format expected by OpenAI API
        api_messages = [{"role": "system", "content": self.system_prompt()}]
        
        # Add history messages (they're already in the correct format)
        api_messages.extend(history)
        
        # Add the current user message
        api_messages.append({"role": "user", "content": message})
        
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=api_messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                api_messages.append(message)
                api_messages.extend(results)
            else:
                done = True
        
        # Get the text response
        text_response = response.choices[0].message.content
        
        # Convert to speech
        audio_file_path = text_to_speech(text_response)
        
        # Return both text and audio file path
        return text_response, audio_file_path


def create_chat_interface():
    """Create a custom chat interface with audio output"""
    me = Me()
    
    with gr.Blocks(title="Career Chatbot with Voice") as demo:
        gr.Markdown("# 🎤 Career Chatbot with Voice")
        gr.Markdown("Chat with Lekha Satnur - now with voice responses!")
        
        chatbot = gr.Chatbot(height=400, type="messages")
        msg = gr.Textbox(label="Type your message here...", placeholder="Ask me about my experience, skills, or background!")
        
        # Audio output component with autoplay
        audio_output = gr.Audio(label="Voice Response", type="filepath", autoplay=True)
        
        def respond(message, history):
            text_response, audio_file_path = me.chat(message, history)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": text_response})
            return history, audio_file_path
        
        msg.submit(respond, [msg, chatbot], [chatbot, audio_output])
        
        # Clear button
        clear = gr.Button("Clear")
        clear.click(lambda: None, None, chatbot, queue=False)
    
    return demo


if __name__ == "__main__":
    demo = create_chat_interface()
    demo.launch()
