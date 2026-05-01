from contextlib import redirect_stderr
import os
import pandas as pd
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory, LangDetectException
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import (
    create_async_playwright_browser,  # A synchronous browser is available, though it isn't compatible with jupyter.\n",   },
)
from playwright.async_api import async_playwright
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_experimental.utilities import PythonREPL
from tempfile import TemporaryDirectory
from langchain_community.agent_toolkits import FileManagementToolkit
import asyncio

load_dotenv(override=True)

def get_url_lang_data_redirect_auto(url: str):
    try:
        response = requests.get(url, timeout=10)  # auto-follow redirects
        current_url = response.url
        status_code = response.status_code
        redirect_occurred = len(response.history) > 0
        if response.text:
            soup = BeautifulSoup(response.text, "html.parser")
            html_tag = soup.find("html")
            html_lang = html_tag.get("lang", "n/a").lower() if html_tag else "n/a"
            lang_normalized = html_lang.split("-")[0]
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            if len(text) < 50:
                detected_lang = "und"
                match = False
            else:
                try:
                    detected_lang = detect(text).lower()
                except LangDetectException:
                    detected_lang = "und"
                match = lang_normalized == detected_lang
            status_info = f"{status_code}{'_redirected' if redirect_occurred else ''}"
            return current_url, html_lang, lang_normalized, detected_lang, match, status_info
        return current_url, "error", "error", "error", False, status_code
    except requests.exceptions.Timeout:
        return url, "error", "error", "error", False, "timeout"
    except requests.exceptions.ConnectionError:
        return url, "error", "error", "error", False, "connection_error"
    except Exception:
        return url, "error", "error", "error", False, "error"

@tool(description="Get page html lang attribute value and compare it with page text tranlation language")
def page_lang_detector(path:str):
    if not os.path.exists(path):
        return f"[File not found: {path}]"
    csv_df = pd.read_csv(path)  # Use full path
    results = csv_df['url'].apply(lambda x: pd.Series(get_url_lang_data_redirect_auto(x)))
    csv_df[["current_url", "lang", "lang_normilized", "lang_from_translation", "match", "status_code"]] = results
    output_path = os.path.join("./.gradio/output", "result.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    csv_df.to_csv(output_path, index=False)
    return output_path

# https://docs.langchain.com/oss/python/integrations/tools/python
python_repl = PythonREPL()
@tool(description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.")
def run_python(code: str):
    return python_repl.run(code)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
@tool(description="Send a push notification to the user")
def push_notification(text: str):
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"

# https://docs.langchain.com/oss/python/integrations/tools/wikipedia
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
@tool(description="Search Wikipedia for relevant information")
def wiki(query: str):
    return wikipedia.run(query)

# https://docs.langchain.com/oss/python/integrations/tools/google_serper
serper = GoogleSerperAPIWrapper()
@tool(description="Search the web using Google Serper API")
def search_web(query: str):
    return serper.run(query)

# https://docs.langchain.com/oss/python/integrations/tools/playwright
async def setup_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        tools = toolkit.get_tools()
        return tools, browser 


# https://docs.langchain.com/oss/python/integrations/tools/filesystem
working_directory = TemporaryDirectory()

def file_management_tools():
    print(working_directory, "WORKING DIRECTORY")
    toolkit = FileManagementToolkit(
        root_dir=working_directory.name
    )  
    return  toolkit.get_tools()

@tool(description="Return the CSV header and first data row as a string snippet for context.")
def read_csv_snippet(file_path: str) -> str:
    if not os.path.exists(file_path):
        return "[File not found]"

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            return "[CSV is empty]"
       
        snippet_df = df.head(1)  
        snippet = snippet_df.to_csv(index=False)
        return snippet
    except Exception as e:
        return f"[Unable to read file: {e}]"

async def all_tools():
    file_tools = file_management_tools()
    playwright_tools, _ = await setup_playwright()
    return file_tools + playwright_tools + [search_web, wiki, push_notification, run_python, read_csv_snippet, page_lang_detector]

if __name__ == "__main__":
    tools = asyncio.run(all_tools())
    print(f"Loaded {tools} tools.")
    

