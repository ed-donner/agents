import requests
import os


def push(text):
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_TOKEN"),
                "user": os.getenv("PUSHOVER_USER"),
                "message": text,
            },
            timeout=5,
        )
    except Exception as e:
        print(f"Pushover failed: {e}")


def record_user_details(email, name="unknown", notes=""):
    push(f"USER: {name}, EMAIL: {email}, NOTES: {notes}")
    return {"status": "ok"}


def record_unknown_question(question):
    push(f"UNKNOWN QUESTION: {question}")
    return {"status": "ok"}


TOOL_REGISTRY = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
}
