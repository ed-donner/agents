from __future__ import annotations

import json
import os
from pathlib import Path
from sys import path
from typing import Any

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from evaluation import evaluate, rerun

# The usual start
load_dotenv(override=True)
openai = OpenAI()

BASE_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = BASE_DIR / "me" / "summary.txt"
CV_PATH = BASE_DIR / "me" / "linkedin.pdf"

print(f"Looking for summary at {SUMMARY_PATH}")
print(f"Looking for CV at {CV_PATH}")

# For pushover
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

if pushover_user:
    print(f"Pushover user found and starts with {pushover_user[0]}")
else:
    print("Pushover user not found")

if pushover_token:
    print(f"Pushover token found and starts with {pushover_token[0]}")
else:
    print("Pushover token not found")


def _extract_pdf_text(pdf_path: Path) -> str:
    # function to extract text from a PDF, returning it as a single string. If the PDF doesn't exist or can't be read, return an empty string
    if not pdf_path.exists():
        return ""

    reader = PdfReader(str(pdf_path))
    text_chunks: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_chunks.append(text)
    return "\n".join(text_chunks)


def _read_summary(summary_path: Path) -> str:
    # function to read the summary from a text file. If the file doesn't exist, return an empty string
    if not summary_path.exists():
        return ""
    return summary_path.read_text(encoding="utf-8")


name = "Norbert Osiemo"
summary = _read_summary(SUMMARY_PATH)
linkedin = _extract_pdf_text(CV_PATH)


def push(message: str) -> dict[str, str]:
    # function that takes a message and sends it as a push notification using the Pushover API. If the PUSHOVER_USER or PUSHOVER_TOKEN environment variables are not set, it should return a dictionary indicating that the push was skipped. If there is an error sending the push notification, it should return a dictionary with the error details. Otherwise, it should return a dictionary indicating that the push was sent successfully.
    print(f"Push: {message}")

    if not pushover_user or not pushover_token:
        return {"status": "skipped", "reason": "PUSHOVER_USER or PUSHOVER_TOKEN missing"}

    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    try:
        response = requests.post(pushover_url, data=payload, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        return {"status": "error", "detail": str(exc)}

    return {"status": "sent"}


def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided") -> dict[str, str]:
    # function to record user details
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question: str) -> dict[str, str]:
    push(f"Recording {question} asked that I couldn't answer")
    return {"recorded": "ok"}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question that couldn't be answered"}
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]

TOOL_MAP = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
}


# This function can take a list of tool calls, and run them.
def handle_tool_calls(tool_calls: list[Any]) -> list[dict[str, str]]:
    # function that takes a list of tool calls, executes the corresponding functions, and returns a list of results in the format expected by the agent. Each tool call will have a function name and arguments, and you should use the TOOL_MAP to find the corresponding function to execute. The result for each tool call should be returned as a dictionary with keys "role", "content", and "tool_call_id". The "role" should be "tool", the "content" should be the JSON string of the result from executing the tool, and "tool_call_id" should be the id of the tool call.
    results: list[dict[str, str]] = []

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments or "{}")
        print(f"Tool called: {tool_name}", flush=True)

        tool = TOOL_MAP.get(tool_name)
        result = tool(**arguments) if tool else {"error": f"Unknown tool: {tool_name}"}
        results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id})

    return results


def _build_system_prompt() -> str:
    # function to build the system prompt for the agent, incorporating the summary and linkedin information, and instructions for how the agent should behave in the conversation. The prompt should instruct the agent to use the tools when appropriate, and to always try to be helpful and engaging in the conversation, while representing Norbert as accurately as possible.
    system_prompt = (
        f"You are acting as {name}. You are answering questions on {name}'s website, "
        f"particularly questions related to {name}'s career, background, skills and experience. "
        f"Your responsibility is to represent {name} for interactions on the website as faithfully as possible. "
        "Your aim is to let potential employers know about your professional background and skills. "
        f"you must be proactive to introduce yourself and profession briefy and ask this potential employer what they could like to know about you as {name}. "
        "Avoid asking potential employers irrelevant questions such 'How can I assist you today?' "
        "You are given a summary of background and LinkedIn profile which you can use to answer questions. "
        "Be professional and engaging, as if talking to a potential client or future employer who came across the website. "
        "If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, "
        "even if it's about something trivial or unrelated to career. "
        "If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email "
        "and record it using your record_user_details tool. "
    )

    system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
    system_prompt += f"With this context, please chat with the user, always staying in character as {name}."
    return system_prompt


system_prompt = _build_system_prompt()


def chat(message: str, history: Any) -> str:
    # function that takes a message and conversation history, and generates a response using the OpenAI API. The function should build the messages list for the API call, starting with the system prompt, followed by the conversation history, and then the latest user message. It should then call the OpenAI API to generate a response, handling any tool calls if necessary. If the response is generated successfully, it should be evaluated using the evaluate function, and if it fails evaluation, it should be rerun with feedback from the evaluator.
    history = history or []
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]

    done = False
    response = None

    while not done:
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            assistant_message = choice.message
            messages.append(assistant_message.model_dump(exclude_none=True))
            tool_results = handle_tool_calls(assistant_message.tool_calls or [])
            messages.extend(tool_results)
        else:
            done = True

    if response is None:
        return "I could not generate a response."

    reply = response.choices[0].message.content or ""
    evaluation = evaluate(reply, message, history, name, summary, linkedin)
    
    print(f"Evaluation result: acceptable={evaluation.is_acceptable}, feedback={evaluation.feedback}")

    if evaluation.is_acceptable:
        print("Passed evaluation - returning reply")
        return reply

    print("Failed evaluation - retrying")
    print(evaluation.feedback)
    return rerun(reply, message, history, evaluation.feedback, system_prompt)


def build_gradio_app() -> gr.ChatInterface:
    # function to build the Gradio app, which should be a chat interface that uses the chat function to generate responses. The app should have a title and description, and should include some example questions that a user might ask. The chatbot should also have an avatar image, which can be found in the "me" directory as "nober.jpg".
    possible_questions = [
        ["What is your professional background?"],
        ["Can you describe your experience in the industry?"],
        ["What are your career highlights?"],
    ]
    avatar_path = str(BASE_DIR / "me" / "nober.jpg")
    # print(f"Looking for avatar image at {avatar_path}")
    chatbot = gr.Chatbot(
    
    avatar_images=(None, avatar_path)
)

    return gr.ChatInterface(
        fn=chat,
        chatbot=chatbot,
        title="Chat with Norbert Osiemo",
        description=(
            "Click a question below to get started.\n\n"
            "Note:This is an AI chatbot, my responses may not be accurate and are limited to current knowledge base only."
        ),
        examples=possible_questions,
    )


__all__ = [
    "chat",
    "build_gradio_app",
    "handle_tool_calls",
    "record_user_details",
    "record_unknown_question",
]
