from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
#from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.tools import GoogleSerperRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from email_sender import send_email


load_dotenv(override=True)

serper = GoogleSerperAPIWrapper()
wikipedia = WikipediaAPIWrapper()

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright

def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


def other_tools():
    file_tools = get_file_tools()

    tool_search = GoogleSerperRun(api_wrapper=serper)
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
    python_repl = PythonREPLTool()
    
    return file_tools + [send_email, tool_search, python_repl,  wiki_tool]

def tool_purpose(all_tools=[]):
    tools = all_tools if all_tools else other_tools()
    msg = "Below are the tools with their name and description:\n"
    for tool in tools:
        msg += f"Name:{tool.name} - Description:{tool.description}\n"
    
    return msg

