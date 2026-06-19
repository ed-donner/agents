from openai import OpenAI
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import gradio as gr
import json

class userLearned(BaseModel):
    isLearned: bool
    topicName: str
    triggeringExample: str

load_dotenv()

gemini = OpenAI()

if os.path.exists("data.json"):
    data = json.load(open("data.json", "r"))
else:
    data = []

def check_user_learnt(user_message, history):
    system_prompt = f"""
    You are a helpful assistant that checks if the user has learned the topic.
    You need to check if the user has learned the topic based on the history of the conversation,
    and what example that triggered the learning.
    The user learned the topic only if they confirm that they understand the topic, and answer a question you asked them correctly.
    Extract if the user has learned the topic, the topic name and the triggering example.
    
    Extract only if the topic is not already in the data.
    if a topic is already in the data, just return not learned.
    
    data: {data}
    """
    messages = [{
        "role": "system",
        "content": system_prompt
    }, {
        "role": "user",
        "content": f"History of the conversation: {history}\n\nUser message: {user_message}"
    }]
    
    response = gemini.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=messages,
        response_format=userLearned
    )
    return response.choices[0].message.parsed

def chat(user_message, history):
    messages = [{
        "role": "system",
        "content": f"""
        You are a helpful assistant that helps the user learn about a topic.
        When the user refers to a topic, you need to check if the user has already learned the topic, 
        if they have, you need to provide them with the same example that triggered the learning so that the student can retrieve the information quickly.
        
        Respond with question to the user, give short answers. Let the users think and you should guide them to learn.
        
        User learnt data: {data}
        """
    }] + history + [{
        "role": "user",
        "content": user_message
    }]
    
    learned = check_user_learnt(user_message, history)
    if learned.isLearned:
        print(f"User has learned the topic: {learned.topicName}")
        data.append({"topicName": learned.topicName, "triggeringExample": learned.triggeringExample})
        json.dump(data, open("data.json", "w"))
        print(f"Data: {data}")
    
    response = gemini.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content



gr.ChatInterface(chat, type="messages").launch()