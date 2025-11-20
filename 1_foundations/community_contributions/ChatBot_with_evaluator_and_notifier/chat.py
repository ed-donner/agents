import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv(override=True)

MODEL = "gpt-4o-mini"


class ChatGPTLLM:
    def __init__(self, model: str = MODEL):
        load_dotenv(override=True)
        self.model = model
        self.client = OpenAI()

    def format_context_prompt(self, query: str, context: List[str]) -> str:
        joined = "\n\n".join(context) if context else "(no context)"
        return (
            "You are a careful, concise assistant. Use ONLY the Context below.\n"
            "If the answer is not present in the Context, reply exactly: I don't know.\n"
            "Do not add external knowledge or speculate.\n\n"
            f"Context:\n{joined}\n\n"
            f"Question: {query}\n"
            "Answer succinctly in 1-3 sentences."
        )

    def generate_response(self, query: str, context: List[str]) -> Dict[str, Any]:
        try:
            prompt = self.format_context_prompt(query, context)
            messages = [
                {"role": "system", "content": "Answer only from provided Context."},
                {"role": "user", "content": prompt},
            ]
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            content = resp.choices[0].message.content
            return {"text": content or "", "raw": json.loads(resp.model_dump_json())}
        except Exception as e:
            print(f"[llm1] error: {e}")
            return {"error": str(e), "text": ""}
