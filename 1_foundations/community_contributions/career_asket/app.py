from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import json
import math
import os
import re
import requests
from collections import Counter
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


_word_re = re.compile(r"[a-zA-Z0-9']+")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _word_re.findall(text)]


def build_chunks(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    if not text:
        return []
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


class Evaluation(BaseModel):
    acceptable: bool
    feedback: str


EVALUATOR_SYSTEM_PROMPT = (
    "You are a strict evaluator of an assistant chatting as a professional career persona. "
    "You will judge whether the assistant response is accurate given the provided context, "
    "professional, and helpful. If it is not acceptable, explain exactly what to fix."
)


class Me:

    def __init__(self):
        self.openai = OpenAI()
        self.name = "Franck Olivier Alex Asket"
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

        self.kb_chunks = build_chunks(self.summary, chunk_size=900, overlap=120) + build_chunks(
            self.linkedin, chunk_size=900, overlap=120
        )

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
    
    def retrieve_context(self, query: str, k: int = 3) -> str:
        q = Counter(_tokens(query))
        if not q or not self.kb_chunks:
            return ""

        scored: list[tuple[float, str]] = []
        for ch in self.kb_chunks:
            c = Counter(_tokens(ch))
            dot = sum(q[t] * c.get(t, 0) for t in q)
            if dot <= 0:
                continue
            qn = math.sqrt(sum(v * v for v in q.values()))
            cn = math.sqrt(sum(v * v for v in c.values()))
            scored.append(((dot / (qn * cn)) if (qn and cn) else 0.0, ch))

        if not scored:
            return ""

        top = [ch for _, ch in sorted(scored, key=lambda x: x[0], reverse=True)[:k]]
        return "\n\n".join(f"[Context {i+1}] {t}" for i, t in enumerate(top))

    def evaluate_reply(self, user_message: str, assistant_reply: str, extra_context: str) -> Evaluation:
        messages = [
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Here is extra context the assistant had available:\n"
                    f"{extra_context}\n\n"
                    "User message:\n"
                    f"{user_message}\n\n"
                    "Assistant reply:\n"
                    f"{assistant_reply}\n\n"
                    "Return JSON with keys: acceptable (bool), feedback (string)."
                ),
            },
        ]
        resp = self.openai.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=Evaluation,
        )
        return resp.choices[0].message.parsed

    def chat(self, message, history):
        dynamic_context = self.retrieve_context(message, k=3)

        messages = [{"role": "system", "content": self.system_prompt()}]
        if dynamic_context:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Additional context (use only if relevant; do not fabricate beyond it):\n"
                        + dynamic_context
                    ),
                }
            )
        messages = messages + history + [{"role": "user", "content": message}]
        done = False
        last_response_text = ""
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                msg = response.choices[0].message
                tool_calls = msg.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(msg)
                messages.extend(results)
            else:
                done = True
                last_response_text = response.choices[0].message.content

        try:
            evaluation = self.evaluate_reply(message, last_response_text, dynamic_context)
            if not evaluation.acceptable:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Revise your last answer using this evaluator feedback. "
                            "If you don't know something, say so and (if appropriate) call record_unknown_question.\n\n"
                            f"Evaluator feedback: {evaluation.feedback}"
                        ),
                    }
                )

                response2 = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=tools,
                )

                if response2.choices[0].finish_reason == "tool_calls":
                    msg2 = response2.choices[0].message
                    results2 = self.handle_tool_call(msg2.tool_calls)
                    messages.append(msg2)
                    messages.extend(results2)

                    response3 = self.openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        tools=tools,
                    )
                    if response3.choices[0].finish_reason != "tool_calls":
                        last_response_text = response3.choices[0].message.content
                else:
                    last_response_text = response2.choices[0].message.content
        except Exception:
            pass

        return last_response_text
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
    