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
from pathlib import Path



load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def get_file_tools():
    # Ensure sandbox directory exists
    sandbox_dir = Path(__file__).parent / "sandbox"
    sandbox_dir.mkdir(exist_ok=True)
    toolkit = FileManagementToolkit(root_dir=str(sandbox_dir))
    return toolkit.get_tools()


def save_file(content: str, filename: str) -> str:
    """
    Save content to a file in the sandbox directory. 
    Supports any file type based on the extension (e.g., .md, .html, .py, .txt, .json, .csv, etc.).
    
    Args:
        content: The content to save
        filename: The filename with extension (e.g., 'report.md', 'data.html', 'script.py')
    
    Returns:
        Success message with file path
    """
    sandbox_dir = Path(__file__).parent / "sandbox"
    sandbox_dir.mkdir(exist_ok=True)
    
    file_path = sandbox_dir / filename
    
    try:
        # Write content to file
        file_path.write_text(content, encoding='utf-8')
        return f"Successfully saved file to: {file_path}"
    except Exception as e:
        return f"Error saving file: {str(e)}"


async def other_tools():
    push_tool = Tool(
        name="send_push_notification", 
        func=push, 
        description="Use this tool when you want to send a push notification to the user"
    )
    
    file_tools = get_file_tools()
    
    save_file_tool = Tool(
        name="save_file",
        func=save_file,
        description="""CRITICAL: Use this tool to save content to a file when the user asks you to create, save, write, or document something in a file.
        
        This tool saves content to a file in the sandbox directory. You MUST use this tool if the user requests:
        - Creating a Markdown document (.md or .markdown)
        - Creating an HTML file (.html)
        - Saving Python code (.py)
        - Creating a text file (.txt)
        - Saving JSON data (.json)
        - Creating a CSV file (.csv)
        - Any other file format
        
        Input format: save_file(content_string, filename_string)
        - First argument: The full content to save as a string
        - Second argument: The filename with extension (e.g., "report.md", "data.html", "script.py")
        
        Examples:
        - To save Markdown: save_file("# Title\n\nContent here", "report.md")
        - To save HTML: save_file("<html><body><h1>Title</h1></body></html>", "page.html")
        - To save Python: save_file("print('Hello')", "script.py")
        
        IMPORTANT: Always use this tool when the user asks you to create, save, or write a file. Do not just mention that you will create it - actually call this tool with the content."""
    )

    tool_search = Tool(
        name="search",
        func=serper.run,
        description="""Use this tool to search the internet for information when the user asks about topics, places, businesses, or anything that requires current information.
        
        This tool performs a Google search and returns relevant results including:
        - Web page titles and snippets
        - URLs to relevant websites
        - Brief summaries of search results
        
        Use this tool when:
        - The user asks about specific places, businesses, or locations (e.g., "hotels in HomaBay Town")
        - You need to find current information about a topic
        - The user asks for recommendations or reviews
        - You need to find websites or resources related to a query
        
        Input: A search query string (e.g., "top hotels in HomaBay Town Kenya", "best restaurants HomaBay Kenya")
        
        After getting search results, you can use the browser navigation tools to visit specific URLs from the results for more detailed information."""
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()
    
    return file_tools + [push_tool, save_file_tool, tool_search, python_repl, wiki_tool]

