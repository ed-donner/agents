import os
import google.generativeai as genai
from google.generativeai import GenerativeModel
import gradio as gr
from dotenv import load_dotenv
from PyPDF2 import PdfReader

# Load environment variables
load_dotenv()
api_key = os.environ.get('GOOGLE_API_KEY')

# Configure Gemini
genai.configure(api_key=api_key)
model = GenerativeModel("gemini-1.5-flash")

# Load profile data
with open("summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

reader = PdfReader("Profile.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

# System prompt
name = "Rishabh Dubey"
system_prompt = f"""
You are acting as {name}. You are answering questions on {name}'s website, 
particularly questions related to {name}'s career, background, skills and experience. 
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. 
You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. 
Be professional and engaging, as if talking to a potential client or future employer who came across the website. 
If you don't know the answer, say so.

## Summary:
{summary}

## LinkedIn Profile:
{linkedin}

With this context, please chat with the user, always staying in character as {name}.
"""

def chat(message, history):
    conversation = f"System: {system_prompt}\n"
    for user_msg, bot_msg in history:
        conversation += f"User: {user_msg}\nAssistant: {bot_msg}\n"
    conversation += f"User: {message}\nAssistant:"

    response = model.generate_content([conversation])
    return response.text

if __name__ == "__main__":
    # Make sure to bind to the port Render sets (default: 10000) for Render deployment
    port = int(os.environ.get("PORT", 10000))
    gr.ChatInterface(chat, chatbot=gr.Chatbot()).launch(server_name="0.0.0.0", server_port=port)
