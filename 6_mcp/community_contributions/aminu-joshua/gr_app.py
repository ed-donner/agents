import json

from openai import OpenAI

CHAT_MODEL = "phi3:latest"
SYSTEM_MESSAGE = """
You are a helpful and friendly travel advisor. 
You assist users in planning their trips by asking relevant questions and providing recommendations based on their preferences. 
Always be polite, engaging, and informative in your responses. Use emojis to make the conversation more enjoyable!

I need you to extract these information from the user to help plan their trip:
- destination
- duration of the trip
- origin: current location of the user
- budget
- travel dates

Once you do, give the user the summary like this

Awesome! Here's what I’ve got:

📍 Destination: 
🕒 Duration: 
🛫 From: 
💵 Budget: 
📅 Travel Dates:
Would you like to go ahead with planning your trip? Answer Yes if so.
"""

openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')

def message_gpt(prompt, chat_history):
    history = [{"role":h["role"], "content":h["content"]} for h in chat_history]
    messages = [{"role": "system", "content": SYSTEM_MESSAGE}] + history + [{"role": "user", "content": prompt}]
    response = openai.chat.completions.create(model=CHAT_MODEL, messages=messages)
    return response.choices[0].message.content

def is_ready_to_plan(text):
    return text.strip().lower() in ["yes", "yeah", "yep", "sure"]

def extract_profile(chat_history):
    prompt = f"""
Extract structured travel info from this conversation.

Return JSON:
{{
  "destination": "",
  "duration": "",
  "origin": "",
  "budget": "",
  "dates": ""
}}

Conversation:
{chat_history}
"""
    res = openai.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content


