from dotenv import load_dotenv
from langchain.agents import Tool
import os
import requests
from langchain_community.agent_toolkits.gmail.toolkit import GmailToolkit
#from langchain_community.utilities import OpenWeatherMapAPIWrapper
from langchain_experimental.tools import PythonREPLTool
load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


async def send_email_tool(): 
    """Send an email to the recipient with the given subject and message"""
    toolkit = GmailToolkit()
    return toolkit.get_tools()

async def all_tools():
    python_repl = PythonREPLTool()
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    return [push_tool, python_repl, send_email_tool]

