import os
import requests
from dotenv import load_dotenv
from agents import function_tool

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")

pushover_url = "https://api.pushover.net/1/messages.json"


def push(text):
    return requests.post(
        pushover_url,
        data={
            "token": pushover_token,
            "user": pushover_user,
            "message": text,
        },
    ).status_code

@function_tool
def record_user_details_tool(email:str, name:str="Name not provided", notes:str="not provided") -> str:
    """ Use this tool to record that a user is interested in being in touch and provided an email address """
    result = push(f"Recording interest from {name} with email {email} and notes {notes}")
    return f"Recording interest pushed with API status code {result}"

@function_tool
def record_unknown_question_tool(question:str) -> str:
    """ Always use this tool to record any question that couldn't be answered as you didn't know the answer """
    push(f"Recording {question} asked that I couldn't answer")
    return "OK"

tools = [record_user_details_tool, record_unknown_question_tool]
