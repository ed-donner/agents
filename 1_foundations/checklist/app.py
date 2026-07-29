from dotenv import load_dotenv
from openai import OpenAI

from context import SYSTEM_PROMPT, USER_MESSAGE
from tools import tools, handle_tool_calls, show, checklist, completed

load_dotenv(override=True)

MODEL_NAME = "gpt-5.4-nano"

openai = OpenAI()


def loop(messages):
    response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    while response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        tool_calls = message.tool_calls
        results = handle_tool_calls(tool_calls)
        messages.append(message)
        messages.extend(results)
        response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    show(response.choices[0].message.content)


if __name__ == "__main__":
    checklist.clear()
    completed.clear()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_MESSAGE},
    ]
    loop(messages)
