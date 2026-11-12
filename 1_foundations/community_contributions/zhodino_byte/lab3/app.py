import json

from dotenv import load_dotenv
import os

from openai import OpenAI
from tools import record_email_tool

load_dotenv(override=True)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

openai = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)

tools = [
    {
        "type": "function",
        "function": {
            "name": "record_email_tool",
            "description": "Records the email address of the user for future reference.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "The email address to be recorded.",
                    }
                },
                "required": ["email"],
            },
        },
    }
]


def chat(message, history):
    messages = (
        [
            {
                "role": "system",
                "content": "You are a american football club assisant. Football club is Minsk Zubrs. You need to answer user questions about the club's history, players, and achievements. If user wants to ask coaches or head of the club, or to come to train he needs to send his email. You need to save this email.",
            }
        ]
        + history
        + [
            {
                "role": "user",
                "content": message,
            }
        ]
    )

    response = openai.chat.completions.create(
        model="gpt-5.4-mini", messages=messages, tools=tools
    )
    while response.choices[0].message.tool_calls:
        message = response.choices[0].message
        messages.append(message)

        for tc in message.tool_calls:
            if tc.function.name == "record_email_tool":
                email = json.loads(tc.function.arguments).get("email")
                record_email_tool(email)
                messages.append(
                    {
                        "role": "tool",
                        "content": "Email recorded",
                        "tool_call_id": tc.id,
                    }
                )
        response = openai.chat.completions.create(
            model="gpt-5.4-mini", messages=messages, tools=tools
        )

    final_answer = response.choices[0].message.content

    return final_answer
