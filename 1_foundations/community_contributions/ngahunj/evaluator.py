from openai import OpenAI
from config import BASE_URL, OPENROUTER_API_KEY, EVAL_MODEL, REQUEST_TIMEOUT
from utils import safe_json_loads


class Evaluator:
    def __init__(self, resume, name):
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key=OPENROUTER_API_KEY,
        )
        self.resume = resume
        self.name = name

    def evaluate(self, reply, user_message, history):
        messages = [
            {
                "role": "system",
                "content": f"You are evaluating responses as {self.name}. Be strict.",
            },
            {
                "role": "user",
                "content": f"""
                Conversation:
                {history}

                User:
                {user_message}

                Reply:
                {reply}

                Respond ONLY in JSON:
                {{
                "is_acceptable": true/false,
                "feedback": "reason"
                }}
                """,
            },
        ]

        try:
            response = self.client.chat.completions.create(
                model=EVAL_MODEL,
                messages=messages,
                timeout=REQUEST_TIMEOUT,
            )

            content = response.choices[0].message.content
            parsed = safe_json_loads(content)

            if parsed:
                return parsed

        except Exception as e:
            print("Evaluation error:", e)

        return {"is_acceptable": True, "feedback": "fallback"}
