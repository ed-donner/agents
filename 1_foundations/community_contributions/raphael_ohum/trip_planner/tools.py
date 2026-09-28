import json
import os
import requests
from dotenv import load_dotenv
from rich.console import Console
from ddgs import DDGS
from ddgs.exceptions import DDGSException

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")

pushover_url = "https://api.pushover.net/1/messages.json"

def push(message):
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)

def show(text):
    try:
        Console().print(text)
    except Exception:
        print(text)

checklist, completed = [], []
def get_checklist_report() -> str:
    result = ""
    for index, item in enumerate(checklist):
        if completed[index]:
            result += f"Checklist #{index + 1}: [green][strike]{item}[/strike][/green]\n"
        else:
            result += f"Checklist #{index + 1}: {item}\n"
    show(result)
    return result

def create_checklist(descriptions: list[str]) -> str:
    checklist.extend(descriptions)
    completed.extend([False] * len(descriptions))
    return get_checklist_report()

def mark_complete(index: int, completion_notes: str) -> str:
    if 1 <= index <= len(checklist):
        completed[index - 1] = True
    else:
        return "No checklist at this index."
    show(completion_notes)
    return get_checklist_report()

def record_user_details(name, destination, no_of_travelers, days, email="Email not provided", notes="not provided"):
    print(f"Tool called to record a user's trip detail: Name: {name}, Destination: {destination}, Travelers: {no_of_travelers}, Days: {days}, Email: {email}, Notes: {notes}")
    with open("trip_records.txt", "a", encoding="utf-8") as f:
        f.write(f"Name: {name}, Destination: {destination}, Travelers: {no_of_travelers}, Days: {days}, Email: {email}, Notes: {notes}\n")
    return "Trip details recorded"

def record_trip_details(name, destination, no_of_travelers, days, email="Email not provided", notes="not provided"):
    if int(no_of_travelers) == 1:
        traveling = "alone"
    elif int(no_of_travelers) > 1:
        traveling = "in a group"
    else:
        traveling = "unknown"
    push(f"Recording trip details from {name} with email {email} and notes {notes} traveling {traveling} to {destination} for {days} days.")
    record = record_user_details(name, destination, no_of_travelers, days, email, notes)
    print(record)
    return "OK"

def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    return "OK"

def search_web(query: str, max_results: int = 5) -> dict:
    """Search the web and return result titles, URLs, and snippets."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if isinstance(max_results, bool) or not 1 <= max_results <= 10:
        raise ValueError("max_results must be an integer from 1 to 10")

    try:
        results = DDGS().text(query, max_results=max_results)
    except DDGSException as exc:
        return {"query": query, "results": [], "error": f"Web search returned no usable results or failed: {exc}",}

    return {
        "query": query,
        "results": [
            {
                "title": item.get("title", ""),
                "url": item.get("href", ""),
                "snippet": item.get("body", "")[:3000],
            }
            for item in results
        ],
    }

record_trip_details_json = {
    "name": "record_trip_details",
    "description": "Record or update the trip details provided by the user. Use null for unknown fields; do not infer values.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": ["string", "null"], "description": "The name of this user"},
            "destination": {"type": ["string", "null"], "description": "The destination this user is interested in traveling to"},
            "no_of_travelers": {"type": ["integer", "null"], "description": "The number of travelers this user is planning for"},
            "days": {"type": ["integer", "null"], "description": "The number of days this user is planning to travel for"},
            "email": {"type": ["string", "null"], "description": "The email address of this user"},
            "notes": {"type": ["string", "null"], "description": "Any additional info about the conversation that's worth recording to give context"}
        },
        "required": ["name", "destination", "no_of_travelers", "days"],
        "additionalProperties": False
    }
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
        "additionalProperties": False
    }
}

search_web_json = {
    "name": "search_web",
    "description": (
        "Search the web for current information. Prefer official attraction, restaurant, and transport-provider websites when checking their details or prices. "
        "Return source URLs with the findings."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query. Use site:domain.com to prioritize a specific official website."},
            "max_results": {"type": "integer", "description": "Number of results to return, from 1 to 10.", "default": 5}
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

create_checklist_json = {
    "name": "create_checklist",
    "description": "Add new checklist from a list of descriptions and return the full list",
    "parameters": {
        "type": "object",
        "properties": {
            "descriptions": {"type": "array", "description": "The descriptions of checklist items", "items": {"type": "string"}},
        },
        "required": ["descriptions"],
        "additionalProperties": False
    }
}

mark_complete_json = {
    "name": "mark_complete",
    "description": "Mark complete the checklist item at the given position (starting from 1) and return the full list",
    "parameters": {
        'properties': {
            'index': {
                'description': 'The 1-based index of the checklist item to mark as complete',
                'title': 'Index',
                'type': 'integer'
                },
            'completion_notes': {
                'description': 'Notes about how you completed the checklist item in rich console markup',
                'title': 'Completion Notes',
                'type': 'string'
                }
            },
        'required': ['index', 'completion_notes'],
        'type': 'object',
        'additionalProperties': False
    }
}

tools = [
            {"type": "function", "function": record_trip_details_json},
            {"type": "function", "function": record_unknown_question_json},
            {"type": "function", "function": search_web_json},
            {"type": "function", "function": create_checklist_json},
            {"type": "function", "function": mark_complete_json}
        ]

tool_handlers = {
    "record_trip_details": record_trip_details,
    "record_unknown_question": record_unknown_question,
    "search_web": search_web,
    "create_checklist": create_checklist,
    "mark_complete": mark_complete
}

def handle_tool_calls(tool_calls):
    results = []

    for tool_call in tool_calls:
        name = tool_call.function.name
        print(f"Tool called: {name}", flush=True)

        try:
            tool = tool_handlers[name]
        except KeyError:
            raise ValueError(f"Unknown tool: {name}") from None

        arguments = json.loads(tool_call.function.arguments)
        if not isinstance(arguments, dict):
            raise ValueError(f"Arguments for {name} must be a JSON object")

        result = tool(**arguments)
        results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id,})

    return results