from dotenv import load_dotenv
from anthropic import Anthropic
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel
from openai import OpenAI


EVALUATOR_MODEL = "gpt-4o-mini"
RETRY_PREFIX = "Let me think and answer better?\n\n"

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


load_dotenv(override=True)
openai_client = OpenAI()

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

tools = [
    {
        "name": "record_user_details",
        "description": record_user_details_json["description"],
        "input_schema": record_user_details_json["parameters"],
    },
    {
        "name": "record_unknown_question",
        "description": record_unknown_question_json["description"],
        "input_schema": record_unknown_question_json["parameters"],
    },
]


class Evaluator:
    """Uses OpenAI (not Anthropic) to judge the agent's latest reply."""
    def __init__(self, name: str, summary: str, linkedin: str, model: str = EVALUATOR_MODEL):
        self.name = name
        self.summary = summary
        self.linkedin = linkedin
        self.model = model
        self.client = openai_client
    def _system_prompt(self) -> str:
        return (
            f"You are an evaluator that decides whether a response to a question is acceptable. "
            f"You are provided with a conversation between a User and an Agent. Your task is to decide "
            f"whether the Agent's latest response is acceptable quality. "
            f"The Agent is playing the role of {self.name} and is representing {self.name} on their website. "
            f"The Agent has been instructed to be professional and engaging, as if talking to a potential "
            f"client or future employer who came across the website. "
            f"The Agent has been provided with context on {self.name} in the form of their summary and "
            f"LinkedIn details. Here's the information:\n\n"
            f"## Summary:\n{self.summary}\n\n"
            f"## LinkedIn Profile:\n{self.linkedin}\n\n"
            f"With this context, evaluate the latest response. "
            f"Mark is_acceptable false if the reply is inaccurate, off-character, unprofessional, "
            f"or fails to use record_unknown_question when the agent clearly did not know the answer."
        )
    def _user_prompt(self, reply: str, message: str, history: list) -> str:
        return (
            f"Here's the conversation between the User and the Agent:\n\n{history}\n\n"
            f"Here's the latest message from the User:\n\n{message}\n\n"
            f"Here's the latest response from the Agent:\n\n{reply}\n\n"
            f"Please evaluate the response."
        )
    def evaluate(self, reply: str, message: str, history: list) -> Evaluation:
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": self._user_prompt(reply, message, history)},
        ]
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=Evaluation,
        )
        return response.choices[0].message.parsed
    
    def log(self, evaluation: Evaluation, message: str) -> None:
        status = "PASS" if evaluation.is_acceptable else "FAIL"
        print(f"\n[EVAL] {status} | user: {message[:80]!r}", flush=True)
        print(f"[EVAL] feedback: {evaluation.feedback}", flush=True)

class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Abdulrazaq Haroon"
        reader = PdfReader("./me/linkedIn.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/ryan_john_summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        self.evaluator = Evaluator(
            name=self.name,
            summary=self.summary,
            linkedin=self.linkedin,
        )

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
    
    def _generate_reply(self, message, history, system=None):
        """Run Anthropic with tools; return final assistant text."""
        messages = history + [{"role": "user", "content": message}]
        system = system or self.system_prompt()
        response = None
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system,
                messages=messages,
                tools=tools,
            )
            if response.stop_reason != "tool_use":
                break
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"Tool called: {block.name}", flush=True)
                    tool_fn = globals().get(block.name)
                    result = tool_fn(**block.input) if tool_fn else {}
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        return "".join(b.text for b in response.content if b.type == "text")
        
    def _rerun_system_prompt(self, failed_reply, feedback):
        return (
            self.system_prompt()
            + "\n\n## Previous answer rejected\n"
            + "You just tried to reply, but quality control rejected your reply.\n"
            + f"## Your attempted answer:\n{failed_reply}\n\n"
            + f"## Reason for rejection:\n{feedback}\n\n"
            + "Please try again with a better answer."
        )

    def chat(self, message, history):
        history = [{"role": h["role"], "content": h["content"]} for h in history]
        if "married" in message.lower() or "marriage" in message.lower():
            system = self.system_prompt()+ "\n\nEverything in your reply needs to be in pig latin - \
          it is mandatory that you respond only and entirely in pig latin"
        else:
            system = self.system_prompt()
        reply = self._generate_reply(message, history, system)
        try:
            evaluation = self.evaluator.evaluate(reply, message, history)
            self.evaluator.log(evaluation, message)
            if not evaluation.is_acceptable:
                print("[EVAL] retrying with improved answer", flush=True)
                improved = self._generate_reply(
                    message,
                    history,
                    system=self._rerun_system_prompt(reply, evaluation.feedback),
                )
                return RETRY_PREFIX + improved
        except Exception as e:
            print(f"[EVAL] skipped — evaluator error: {e}", flush=True)
        return reply
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    