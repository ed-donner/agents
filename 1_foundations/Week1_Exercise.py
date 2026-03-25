from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import csv 
from pydantic import BaseModel 
import gradio as gr


load_dotenv(override=True)

google_model = "google/gemini-2.5-flash"
gemini_url = "https://openrouter.ai/api/v1"
gemini = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"), 
    base_url=gemini_url)

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
        self.openai = OpenAI()
        self.name = "Nikhil Suresh"
        self.linkedin = ""
        # #    Read CSV Content  

        with open("me-nik/Profile.csv", 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Combine all columns into readable format
                row_text = " | ".join([f"{key}: {value}" for key, value in row.items() if value.strip()])
                if row_text:
                    self.linkedin += row_text + "\n"



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

        system_prompt += f"## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    def evaluator_system_prompt(self):
        evaluator_system_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
The Agent is playing the role of {self.name} and is representing {self.name} on their website. \
The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
The Agent has been provided with context on {self.name} in the form of their LinkedIn details. Here's the information:"
        evaluator_system_prompt += f"## LinkedIn Profile:\n{self.linkedin}\n\n"
        return evaluator_system_prompt 

    def evaluator_user_prompt(self, reply, message, history):
        prompt = f"## Conversation History:\n"
        for msg in history[-3:]:  # Last 3 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            prompt += f"{role.capitalize()}: {content}\n"
        
        prompt += f"\n## Latest User Message:\n{message}\n"
        prompt += f"\n## Agent's Reply:\n{reply}\n"
        prompt += f"\nIs this reply acceptable? Consider if it's professional, accurate based on {self.name}'s profile, and appropriately represents them. Reply with 'acceptable' if good, or explain what needs improvement."
        return prompt
    def evaluate(self, reply, message, history):
        messages = [{"role": "system", "content": self.evaluator_system_prompt()}] + [{"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}]
        response = gemini.chat.completions.create(model=google_model, messages=messages)
        evaluation_text = response.choices[0].message.content
        
        # Create a simple object to check acceptability
        class EvaluationResult:
            def __init__(self, text):
                self.feedback = text
                self.is_acceptable = "acceptable" in text.lower() or "good" in text.lower() or "passed" in text.lower()
        
        return EvaluationResult(evaluation_text)
    def rerun(self, reply, message, history, feedback):
        updated_system_prompt = self.system_prompt() + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
        response = gemini.chat.completions.create(model=google_model, messages=messages)
        return response.choices[0].message.content  
    def chat(self, message, history):

    # Check for patent keyword and modify system prompt accordingly
        if "patent" in message.lower():
            system = self.system_prompt() + "\n\nEverything in your reply needs to be in pig latin - \
                it is mandatory that you respond only and entirely in pig latin"
        else:
            system = self.system_prompt()
        
        messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": message}]
        
        # Handle tool calls loop
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason == "tool_calls":
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(response_message)
                messages.extend(results)
            else:
                done = True
        
        reply = response.choices[0].message.content
        
        # Evaluation step
        evaluation = self.evaluate(reply, message, history)
        
        if evaluation.is_acceptable:
            print("Passed evaluation - returning reply")
            return reply
        else:
            print("Failed evaluation - retrying")
            print(evaluation.feedback)
            reply = self.rerun(reply, message, history, evaluation.feedback)
            return reply
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    