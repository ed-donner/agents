import json
from openai import OpenAI
from pypdf import PdfReader

from config import (
    BASE_URL,
    OPENROUTER_API_KEY,
    CHAT_MODEL,
    REQUEST_TIMEOUT,
    EVALUATION_MAX_RETRIES,
)
from prompts import build_system_prompt
from tools import TOOL_REGISTRY
from evaluator import Evaluator
from utils import extract_tool_call


class Agent:
    def __init__(self):
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key=OPENROUTER_API_KEY,
        )
        self.name = "Nahunj"
        self.resume = self.load_resume()
        self.evaluator = Evaluator(self.resume, self.name)

    def load_resume(self):
        try:
            reader = PdfReader("me/resume.pdf")
            text = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t
            return text or "Resume unavailable"
        except Exception as e:
            print("Resume error:", e)
            return "Resume unavailable"

    def call_model(self, messages):
        for _ in range(3):
            try:
                return self.client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=messages,
                    timeout=REQUEST_TIMEOUT,
                )
            except Exception as e:
                print("Retrying model call:", e)
        raise Exception("Model failed after retries")

    def handle_tool(self, text):
        parsed = extract_tool_call(text)
        if not parsed:
            return None

        tool_name, args = parsed
        tool = TOOL_REGISTRY.get(tool_name)

        if not tool:
            print("Unknown tool:", tool_name)
            return None

        try:
            tool(**args)
        except Exception as e:
            print("Tool error:", e)

        return "Thanks! I've recorded that."

    def chat(self, message, history):
        messages = [
            {"role": "system", "content": build_system_prompt(self.name, self.resume)},
            *history,
            {"role": "user", "content": message},
        ]

        try:
            response = self.call_model(messages)
            reply = response.choices[0].message.content
        except Exception:
            return "Something went wrong. Try again."

        # --- TOOL HANDLING ---
        tool_response = self.handle_tool(reply)
        if tool_response:
            return tool_response

        if not reply:
            return "Could you clarify your question?"

        # --- EVALUATION LOOP ---
        retries = 0
        evaluation = self.evaluator.evaluate(reply, message, history)

        while retries < EVALUATION_MAX_RETRIES and not evaluation.get("is_acceptable"):
            retries += 1

            messages.append(
                {
                    "role": "system",
                    "content": f"Improve your last answer: {evaluation.get('feedback')}",
                }
            )

            try:
                response = self.call_model(messages)
                reply = response.choices[0].message.content
            except Exception:
                break

            evaluation = self.evaluator.evaluate(reply, message, history)

        return reply
