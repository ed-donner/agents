from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import gradio as gr
from answer import fetch_context
from pydantic import BaseModel

load_dotenv(override=True)

## First Create a me folder and add your linkedin.pdf and summary.txt files to it
## Then run the app.py file
## You can then chat with the app by typing in the input box and clicking the send button
## The app will respond with a response based on the context of your linkedin.pdf and summary.txt files
## You can also use the tools to record user details and unknown questions
## The app will record the user details and unknown questions in the me folder
## The app will also push notifications to your phone via Pushover

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


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
            },
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


def normalize_history(history):
    """Strip Gradio history to only role and content for OpenAI API (avoids 400 Invalid input)."""
    if not history:
        return []
    out = []
    for msg in history:
        if isinstance(msg, dict):
            content = msg.get("content")
            if content is not None and not isinstance(content, str):
                content = str(content) if content else ""
            out.append({"role": msg["role"], "content": content or ""})
        else:
            # Legacy tuple format (user_msg, assistant_msg)
            if isinstance(msg, (list, tuple)) and len(msg) >= 2:
                out.append({"role": "user", "content": msg[0] if isinstance(msg[0], str) else str(msg[0])})
                out.append({"role": "assistant", "content": msg[1] if isinstance(msg[1], str) else str(msg[1])})
    return out


class Me:

    def __init__(self):
        self.openai = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL")
        )
        self.name = "Cynthia Omovoiye"

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool", "content": json.dumps(
                result), "tool_call_id": tool_call.id})
        return results

    def evaluator_system_prompt(self, relevant_context: str):
        return f"You are an evaluator that decides whether a response to a question is acceptable. \
You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
The Agent is playing the role of {self.name} and is representing {self.name} on their website. \
The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
The Agent has been provided with context on {self.name}. Here's the information: \
## Relevant context about {self.name}: \
{relevant_context} \
With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."

    def system_prompt(self, relevant_context: str):
        return f"""You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
Use the following relevant information about {self.name} to answer. If the user asks something not covered here, say you don't have that information and offer to connect via email. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool.

## Relevant context about {self.name}:
{relevant_context}

With this context, please chat with the user, always staying in character as {self.name}."""

    def rerun(self, reply, message, history, relevant_context, feedback):
        updated_system_prompt = self.system_prompt(relevant_context) + \
            "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = [{"role": "system", "content": updated_system_prompt}
                    ] + normalize_history(history) + [{"role": "user", "content": message}]
        rerun_done = False
        while not rerun_done:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                rerun_done = True
        reply = response.choices[0].message.content
        return reply

    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
        user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return user_prompt

    def evaluate(self, reply, message, history, relevant_context) -> Evaluation:

        messages = [{"role": "system", "content": self.evaluator_system_prompt(relevant_context)
                     }] + [{"role": "user", "content": self.evaluator_user_prompt(reply, message, history)}]
        response = self.openai.chat.completions.parse(
            model="gpt-4o-mini", messages=messages, response_format=Evaluation)
        return response.choices[0].message.parsed

    def chat(self, message, history):
        user_message = message  # preserve; loop overwrites message
        docs = fetch_context(user_message)
        relevant_context = "\n\n".join(doc.page_content for doc in docs)
        messages = [{"role": "system", "content": self.system_prompt(
            relevant_context)}] + normalize_history(history) + [{"role": "user", "content": user_message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason == "tool_calls":
                assistant_message = response.choices[0].message
                tool_calls = assistant_message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(assistant_message)
                messages.extend(results)
            else:
                done = True
        reply = response.choices[0].message.content
        evaluation = self.evaluate(reply, user_message, history, relevant_context)
        if evaluation.is_acceptable:
            return reply
        else:
            print("Failed evaluation - retrying")
            print(evaluation.feedback)
            reply = self.rerun(reply, user_message, history,
                               relevant_context, evaluation.feedback)
            return reply


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()


## deployed to https://huggingface.co/spaces/CynthiaOmovoiye/career_conversation