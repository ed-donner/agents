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

def record_unfounded_response(question, response, missing_context):
    push(f"Unfounded response detected - Q: {question} | A: {response} | Missing: {missing_context}")
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

record_unfounded_response_json = {
    "name": "record_unfounded_response",
    "description": "Use this tool to record when you provided a response that wasn't grounded in the provided context documents",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The original question asked"
            },
            "response": {
                "type": "string",
                "description": "The response that was given"
            },
            "missing_context": {
                "type": "string",
                "description": "What specific information was missing from the context that led to an unfounded response"
            }
        },
        "required": ["question", "response", "missing_context"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json},
        {"type": "function", "function": record_unfounded_response_json}]


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Segundo Juan"
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        
        # Store all context for evaluation
        self.all_context = f"SUMMARY: {self.summary}\n\nLINKEDIN: {self.linkedin}"

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
    
    def evaluate_response(self, question, response):
        """
        Evaluate if the response is grounded in the provided context
        Returns True if response is well-grounded, False otherwise
        """
        evaluation_prompt = f"""
You are an evaluator that checks if a response is properly grounded in the provided context documents.

CONTEXT DOCUMENTS:
{self.all_context}

USER QUESTION: {question}
LLM RESPONSE: {response}

Evaluate if the response is:
1. DIRECTLY SUPPORTED by the context documents
2. REASONABLE INFERENCE from the context documents  
3. COMPLETELY UNFOUNDED (made up information not in context)

For each claim or statement in the response, determine if it's supported by the context.

If the response contains ANY unfounded claims, return FALSE and explain what's missing.
If the response is well-grounded, return TRUE.

Respond with JSON format:
{{
    "is_grounded": true/false,
    "missing_context": "description of what's missing (if any)",
    "reasoning": "brief explanation"
}}
"""
        
        try:
            eval_response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": evaluation_prompt}],
                response_format={"type": "json_object"}
            )
            
            evaluation = json.loads(eval_response.choices[0].message.content)
            return evaluation
            
        except Exception as e:
            print(f"Evaluation error: {e}")
            # Default to assuming response is grounded if evaluation fails
            return {"is_grounded": True, "missing_context": "", "reasoning": "Evaluation failed"}
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
IMPORTANT: Only answer questions based on the information provided in your context documents. If you don't have information about something, \
say you don't know rather than making up an answer. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email, name and if they have any notes and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
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
        
        final_response = response.choices[0].message.content
        
        # Evaluate the response
        evaluation = self.evaluate_response(message, final_response)
        print(f"Evaluation result: {evaluation}")  # Debug print
        
        # If response is not grounded, record it and potentially modify the response
        if not evaluation.get("is_grounded", True):
            print(f"Unfounded response detected: {evaluation}")  # Debug print
            
            # Record the unfounded response directly
            record_unfounded_response(
                question=message,
                response=final_response,
                missing_context=evaluation.get('missing_context', 'Unknown')
            )
            
            # Optionally modify the response to be more honest
            if "don't know" not in final_response.lower() and "not mentioned" not in final_response.lower():
                # Add a disclaimer if the response seems confident but isn't grounded
                final_response += f"\n\n[Note: I should mention that I don't have specific information about this in my background documents. Please take this response with appropriate caution.]"
        
        return final_response
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    