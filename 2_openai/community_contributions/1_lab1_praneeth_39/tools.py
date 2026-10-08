import json
import os
import requests
from dotenv import load_dotenv
from agents import function_tool

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")

pushover_url = "https://api.pushover.net/1/messages.json"


def send_push(message: str) -> None:
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)

@function_tool
def push_tool(message: str) -> str:
    """Send given message to the user as a push notification"""
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    result = requests.post(pushover_url, data=payload).status_code
    return f"Push sent with API status code {result}"

@function_tool
def record_user_details(email: str, name: str="Name not provided", notes: str="not provided") -> str:
    """record a visitors connection details to get in touch"""
    send_push(f"Recording interest from {name} with email {email} and notes {notes}")
    return "Contact recorded"

@function_tool
def record_unknown_question(question: str) -> str:
    """Record a career-related question the digital twin cannot answer."""
    send_push(f"Recording {question} asked that I couldn't answer")
    return "Question recorded"


TWIN_TOOLS = [record_user_details, record_unknown_question]