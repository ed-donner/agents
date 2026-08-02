
from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper




load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()


def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")

    google_scholar_tool = Tool(name="google_scholar", func=serper.run, description="Use this tool when you want to search for papers on Google Scholar")

    return [push_tool, google_scholar_tool]

