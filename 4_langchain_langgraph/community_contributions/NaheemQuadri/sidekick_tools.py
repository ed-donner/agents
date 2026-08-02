from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from pydantic import BaseModel
from langchain_core.tools import StructuredTool



load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()

class EmailInput(BaseModel):
    subject: str
    html_body: str

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"

def send_email(subject: str, html_body: str) -> dict:
    """Send an email to the user using Mailgun"""
    domain = os.getenv("MAILGUN_DOMAIN")
    response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", os.getenv("MAILGUN_API_KEY")),
            data={
                "from":    os.getenv("MAILGUN_FROM_EMAIL"),
                "to":      [os.getenv("MAILGUN_RECIPIENT")],
                "subject": subject,
                "html":    html_body,
            },
        )
    response.raise_for_status()
    print("Mailgun response:", response.status_code)
    return {"status": "success", "status_code": response.status_code}


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    email_tool = StructuredTool.from_function(
        func=send_email,
        name="send_email",
        description="Use this tool when you want to send an email to the user",
        args_schema=EmailInput,
    )
    file_tools = get_file_tools()

    tool_search =Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()
    
    return file_tools + [push_tool, tool_search, python_repl,  wiki_tool, email_tool]

