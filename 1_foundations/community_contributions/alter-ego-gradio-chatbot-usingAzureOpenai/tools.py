from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"


def push(message):
    """Send a push notification via Pushover API."""
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    try:
        requests.post(pushover_url, data=payload)
    except Exception as e:
        print(f"Error sending push notification: {e}")


def record_user_details(email, name="Name not provided", notes="not provided"):
    """
    Record user contact details when they express interest.
    
    Args:
        email (str): User's email address
        name (str): User's name (optional)
        notes (str): Additional context about the conversation
        
    Returns:
        dict: Status confirmation
    """
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok", "message": "Thank you! Your information has been recorded."}


def record_unknown_question(question):
    """
    Log questions that the agent couldn't answer for future improvement.
    
    Args:
        question (str): The question that couldn't be answered
        
    Returns:
        dict: Status confirmation
    """
    push(f"Unknown question asked: {question}")
    return {"recorded": "ok", "message": "Question logged for follow-up."}


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

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered",
            },
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

TOOLS = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]


def handle_tool_calls(tool_calls):
    tool_mapping = {
        "record_user_details": record_user_details,
        "record_unknown_question": record_unknown_question,
    }

    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name}", flush=True)

        tool = tool_mapping.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")

        result = tool(**arguments)
        results.append(
            {
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id,
            }
        )
    return results
