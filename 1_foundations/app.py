from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader
from supabase import create_client
import gradio as gr
import json
import os
import requests


load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = "gpt-5-nano-2025-08-07"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def push(text: str):
    if not PUSHOVER_USER or not PUSHOVER_TOKEN:
        print(f"Push skipped: {text}")
        return

    requests.post(
        PUSHOVER_URL,
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": text,
        },
        timeout=15,
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question, answer=None):
    supabase.table("qa_store").insert(
        {
            "question": question,
            "answer": answer,
            "status": "unknown",
        }
    ).execute()

    push(f"Recording {question} asked that I couldn't answer")
    return {"status": "recorded_unknown"}


def save_qa(question, answer):
    supabase.table("qa_store").insert(
        {
            "question": question,
            "answer": answer,
            "status": "answered",
        }
    ).execute()
    return {"status": "saved"}


def search_qa(question):
    res = (
        supabase.table("qa_store")
        .select("question, answer")
        .ilike("question", f"%{question}%")
        .eq("status", "answered")
        .limit(3)
        .execute()
    )
    return {"results": [(row["question"], row["answer"]) for row in res.data]}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user",
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it",
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

# Keep only true action tools in the tool list.
tools = [{"type": "function", "function": record_user_details_json}]


class Evaluation(BaseModel):
    can_answer: bool
    reason: str


class Me:
    def __init__(self):
        self.openai = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        self.name = "Naman"

        reader = PdfReader("me/myprofile.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text

        with open("me/mysummary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

        self._system_prompt = self._build_system_prompt()
        self._evaluator_system_prompt = self._build_evaluator_system_prompt()

    def _build_system_prompt(self):
        system_prompt = f"""
You are acting as {self.name}. You are answering questions on {self.name}'s website,
particularly questions related to {self.name}'s career, background, skills and experience.

Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible.
You are given a summary of {self.name}'s background and LinkedIn profile, along with relevant past Q&A, which you must use to answer questions.

Be professional and engaging, as if talking to a potential client or future employer.

Rules:
- Only answer questions using information explicitly available in the provided Summary, LinkedIn Profile, or Past Q&A.
- If the information is not explicitly available in the provided context, respond with a short and direct statement such as:
  "I don't have enough information to answer that.". Do not elaborate, speculate, or provide generic alternatives.
- Do NOT fabricate personal preferences, opinions, or facts.
- If the user is engaging in discussion, you may steer the conversation toward getting in touch and ask for their email.

Stay in character as {self.name} at all times.
"""
        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        return system_prompt

    def _build_evaluator_system_prompt(self):
        prompt = f"""
You are an evaluator.

Given a user question and an agent's reply, determine:
- Can the reply be fully supported using ONLY the provided context (summary + linkedin + retrieved Q&A)?

Return:
- can_answer: true/false
- reason: short explanation

Rules:
- If the reply contains fabricated personal preferences or facts not in context, can_answer = false
- If the reply is grounded in context, can_answer = true

The Agent is playing the role of {self.name} and is representing {self.name} on their website.
The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website.
The Agent has been provided with context on {self.name} in the form of their summary and profile details. Here's the information:
"""
        prompt += f"\n\n## Summary:\n{self.summary}\n\n## CV Profile:\n{self.linkedin}\n\n"
        prompt += "With this context, please evaluate the latest response, following the rules provided earlier."
        return prompt

    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = f"Here's the conversation history between the User and the Agent:\n\n{history}\n\n"
        user_prompt += f"Here's the latest message from the User:\n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent:\n\n{reply}\n\n"
        user_prompt += "Please evaluate the response based on rules and context provided to you, replying with whether it is answerable and your feedback."
        return user_prompt

    def evaluate(self, reply, message, history) -> Evaluation:
        messages = [
            {"role": "system", "content": self._evaluator_system_prompt},
            {"role": "user", "content": self.evaluator_user_prompt(reply, message, history)},
        ]
        response = self.openai.chat.completions.parse(
            model=OPENAI_MODEL,
            messages=messages,
            response_format=Evaluation,
        )
        return response.choices[0].message.parsed

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id,
                }
            )
        return results

    def chat(self, message, history):
        retrieved = search_qa(message)

        retrieval_context = ""
        if retrieved["results"]:
            retrieval_context = "\n\n## Past Q&A:\n"
            for question, answer in retrieved["results"]:
                retrieval_context += f"Q: {question}\nA: {answer}\n"

        messages = (
            [
                {"role": "system", "content": self._system_prompt},
                {"role": "system", "content": retrieval_context},
            ]
            + history
            + [{"role": "user", "content": message}]
        )

        while True:
            response = self.openai.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=tools,
            )

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                assistant_message = choice.message
                tool_calls = assistant_message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(assistant_message)
                messages.extend(results)
                continue

            reply = choice.message.content
            evaluation = self.evaluate(reply, message, history)

            if not evaluation.can_answer:
                record_unknown_question(message, reply)
            else:
                save_qa(message, reply)

            return reply


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
