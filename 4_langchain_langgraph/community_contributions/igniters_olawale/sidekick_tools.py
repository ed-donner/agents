import os
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from langchain.agents import Tool
from langchain_core.tools import StructuredTool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from playwright.async_api import async_playwright


load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()

mailtrap_smtp_host = os.getenv("MAILTRAP_SMTP_HOST", "sandbox.smtp.mailtrap.io")
mailtrap_smtp_port = int(os.getenv("MAILTRAP_SMTP_PORT", "2525"))

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def send_mailtrap_email(subject: str, html_body: str) -> dict:
    user = os.environ.get("MAILTRAP_SMTP_USER")
    password = os.environ.get("MAILTRAP_SMTP_PASSWORD")
    host = mailtrap_smtp_host
    port = mailtrap_smtp_port

    if not user or not password:
        return {
            "status": "skipped",
            "message": "MAILTRAP_SMTP_USER or MAILTRAP_SMTP_PASSWORD not set",
        }

    from_addr = os.environ.get("MAILTRAP_FROM", "sender@example.com")
    to_addr = os.environ.get("MAILTRAP_TO", "adeogun161@gmail.com")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.login(user, password)
            s.sendmail(from_addr, [to_addr], msg.as_string())
        return {"status": "success"}
    except Exception as e:
        return {
            "status": "error",
            "message": str(e).strip() or "Send failed",
        }


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    mailtrap_tool = StructuredTool.from_function(
        name="send_email_mailtrap",
        description="Send an HTML email via Mailtrap SMTP. Provide subject and html_body (HTML string).",
        func=send_mailtrap_email,
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
    
    return file_tools + [push_tool, mailtrap_tool, tool_search, python_repl,  wiki_tool]
