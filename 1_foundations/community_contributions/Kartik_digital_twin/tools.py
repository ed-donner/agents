import json
import os
import requests

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")

pushover_url = "https://api.pushover.net/1/messages.json"

def push(message):
    payload = {"user":pushover_user, "token":pushover_token, "message":message}
    response = requests.post(pushover_url, data=payload)
    

def record_user_details(email, name="name not provided", notes ="not provided"):
    push(f"Recording interest from {name} with the {email} and {notes}")
    return "OK"

def record_unknown_question(question):
    push(f"Recording {question} asked that i couldn't answer")
    return "OK"

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {"type": "string", "description": "Any additional info about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description":"""Use this tool whenever the user asks a question that is
outside the information available about the person being represented,
including unrelated general-knowledge questions or personal questions
about the person that are not in the profile. Do not answer such questions
without calling this tool first.""",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question that couldn't be answered"},
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]

tool_map = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question
}

def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name}", flush=True)
        tool = tool_map.get(tool_name)
        result = tool(**arguments) if tool else "No tool found"
        results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
    return results