import json
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

GUPSHUP_TOKEN = os.getenv("GUPSHUP_TOKEN")
DESTINATION = os.getenv("DESTINATION")
RECORD_UNKNOWN_QUESTION = os.getenv("RECORD_UNKNOWN_QUESTION")
RECORD_USER_DETAIL = os.getenv("RECORD_USER_DETAIL")

channel_url = "https://channel-dev.lupai.app/lupai/start_message"


def push(template_id, params):
    requests.post(
        channel_url,
        data={
            "token": GUPSHUP_TOKEN,
            "user_id": f"whatsapp:{DESTINATION}",
            "conversation_id": "LupaiKanban",
            "message": f"--template:{template_id}",
            "params": params
        },
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(RECORD_USER_DETAIL, [name, email, notes])
    return "OK"


def record_unknown_question(question):
    push(RECORD_UNKNOWN_QUESTION, [question])
    return "OK"


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
                "description": "Any additional info about the conversation that's worth recording to give context",
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
            "question": {"type": "string", "description": "The question that couldn't be answered"},
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]

tool_map = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
}


def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name}", flush=True)
        tool = tool_map.get(tool_name)
        result = tool(**arguments) if tool else "Unknown tool: " + tool_name
        results.append(
            {"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id}
        )
    return results
