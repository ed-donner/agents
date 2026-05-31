"""
HALI — HPV Awareness & Learning Initiative
Tool functions, JSON schemas, and tool dispatcher.
"""

import json
import os
import requests

# Pushover notification helper

def push(message: str) -> None:
    """Send a push notification via Pushover. Silently skips if keys are absent."""
    print(f"[PUSH] {message}")
    user = os.getenv("PUSHOVER_USER")
    token = os.getenv("PUSHOVER_TOKEN")
    if user and token:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"user": user, "token": token, "message": message},
        )


# Tool functions

def record_interest(
    name: str,
    location: str,
    contact: str = "not provided",
    notes: str = "not provided",
) -> dict:
    """Record a caregiver or patient who wants to get vaccinated or learn more."""
    push(f"New interest: {name} in {location} | Contact: {contact} | Notes: {notes}")
    return {"recorded": "ok", "message": "Details recorded. A health worker will be in touch."}


def record_unknown_question(question: str, mode: str = "caregiver") -> dict:
    """Record a question that could not be confidently answered."""
    push(f"[{mode.upper()} - UNANSWERED] {question}")
    return {"recorded": "ok"}


def check_eligibility(age: int, gender: str = "female", prior_doses: int = 0) -> dict:
    """
    Check HPV vaccine eligibility under Kenya's national programme.
    Kenya switched to a single-dose schedule in October 2025.
    """
    female_terms = {"female", "girl", "woman", "msichana", "mwanamke", "f"}

    if gender.lower() in female_terms:
        if prior_doses >= 1:
            return {
                "eligible": False,
                "message": "Already vaccinated — one dose is sufficient under Kenya's current schedule.",
                "age": age,
            }
        if 10 <= age <= 14:
            return {
                "eligible": True,
                "message": (
                    "Eligible for routine HPV vaccination. "
                    "Available free at school or nearest health facility. Single dose required."
                ),
                "age": age,
            }
        if age > 14:
            return {
                "eligible": True,
                "message": (
                    "Eligible for catch-up HPV vaccination at a health facility. "
                    "Single dose, free of charge."
                ),
                "age": age,
            }
        return {
            "eligible": False,
            "message": "Below minimum age (10). Check back when the child turns 10.",
            "age": age,
        }

    return {
        "eligible": False,
        "message": (
            "Kenya's HPV programme currently targets girls and women. "
            "Boys and men may benefit — consult a health worker."
        ),
        "age": age,
    }


# Tool JSON schemas (OpenAI function-calling format)

RECORD_INTEREST_SCHEMA = {
    "name": "record_interest",
    "description": (
        "Record that a caregiver or patient wants HPV vaccination or more information. "
        "Use whenever someone expresses interest or provides contact details."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name of the person"},
            "location": {"type": "string", "description": "Their location, county, or village in Kenya"},
            "contact": {"type": "string", "description": "Phone number or other contact if provided"},
            "notes": {"type": "string", "description": "Any relevant notes about their situation or concerns"},
        },
        "required": ["name", "location"],
        "additionalProperties": False,
    },
}

RECORD_UNKNOWN_QUESTION_SCHEMA = {
    "name": "record_unknown_question",
    "description": (
        "Record any question you cannot confidently answer. "
        "Always use this rather than guessing at medical facts."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question that could not be answered"},
            "mode": {"type": "string", "description": "Either 'caregiver' or 'chw'"},
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

CHECK_ELIGIBILITY_SCHEMA = {
    "name": "check_eligibility",
    "description": "Check if a person is eligible for HPV vaccination under Kenya's national programme.",
    "parameters": {
        "type": "object",
        "properties": {
            "age": {"type": "integer", "description": "Age of the person in years"},
            "gender": {"type": "string", "description": "Gender of the person (female/male or Swahili equivalent)"},
            "prior_doses": {"type": "integer", "description": "Number of HPV vaccine doses already received (default 0)"},
        },
        "required": ["age"],
        "additionalProperties": False,
    },
}

TOOLS = [
    {"type": "function", "function": RECORD_INTEREST_SCHEMA},
    {"type": "function", "function": RECORD_UNKNOWN_QUESTION_SCHEMA},
    {"type": "function", "function": CHECK_ELIGIBILITY_SCHEMA},
]

# Map tool names to callables — avoids a giant if-statement (Lab 4 pattern)
TOOL_REGISTRY = {
    "record_interest": record_interest,
    "record_unknown_question": record_unknown_question,
    "check_eligibility": check_eligibility,
}


# Tool dispatcher

def handle_tool_calls(tool_calls) -> list[dict]:
    """Execute a list of tool calls and return formatted result messages."""
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(f"Tool called: {tool_name} | Args: {arguments}", flush=True)
        tool_fn = TOOL_REGISTRY.get(tool_name)
        result = tool_fn(**arguments) if tool_fn else {"error": f"Unknown tool: {tool_name}"}
        results.append({
            "role": "tool",
            "content": json.dumps(result),
            "tool_call_id": tool_call.id,
        })
    return results
