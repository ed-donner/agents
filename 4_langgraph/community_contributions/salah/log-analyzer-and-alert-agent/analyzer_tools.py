from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit, FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper, WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain.agents import Tool
from dotenv import load_dotenv
import os
import requests
from typing import List, Tuple, Optional


load_dotenv(override=True)


class AnalyzerTools:

    @staticmethod
    async def setup_playwright_tools():
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        tools = toolkit.get_tools()
        return tools, browser, playwright

    @staticmethod
    def setup_file_tools(root_dir: str = "."):
        toolkit = FileManagementToolkit(root_dir=root_dir)
        return toolkit.get_tools()

    @staticmethod
    def setup_search_tool():
        serper = GoogleSerperAPIWrapper()
        search_tool = Tool(
            name="search",
            func=serper.run,
            description="Search the web for information about errors, solutions, and best practices. "
                       "Input should be a search query string."
        )
        return search_tool

    @staticmethod
    def setup_wikipedia_tool():
        wikipedia = WikipediaAPIWrapper()
        wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
        return wiki_tool

    @staticmethod
    def setup_python_repl_tool():
        python_repl = PythonREPLTool()
        return python_repl

    @staticmethod
    def setup_notification_tool():
        pushover_token = os.getenv("PUSHOVER_TOKEN")
        pushover_user = os.getenv("PUSHOVER_USER")
        pushover_url = "https://api.pushover.net/1/messages.json"

        def send_push_notification(message: str) -> str:
            if not pushover_token or not pushover_user:
                return "Notification skipped: PUSHOVER_TOKEN or PUSHOVER_USER not configured"

            try:
                response = requests.post(
                    pushover_url,
                    data={
                        "token": pushover_token,
                        "user": pushover_user,
                        "message": message
                    }
                )
                if response.status_code == 200:
                    return "Notification sent successfully"
                else:
                    return f"Notification failed: {response.status_code}"
            except Exception as e:
                return f"Notification error: {str(e)}"

        push_tool = Tool(
            name="send_push_notification",
            func=send_push_notification,
            description="Send a well-formatted push notification about critical errors. "
                       "Input should be a descriptive message including: alert title, error count/types, "
                       "affected components (files/lines), root cause summary, impact statement, and "
                       "recommended actions. Format with clear sections and bullet points for readability. "
                       "Keep under 300 words but be informative and actionable."
        )
        return push_tool

    @staticmethod
    async def setup_all_tools(root_dir: str = ".", enable_browser: bool = False) -> Tuple[List, Optional[object], Optional[object]]:
        browser = None
        playwright = None
        browser_tools = []

        if enable_browser:
            try:
                browser_tools, browser, playwright = await AnalyzerTools.setup_playwright_tools()
            except Exception:
                pass

        file_tools = AnalyzerTools.setup_file_tools(root_dir)

        search_tool = AnalyzerTools.setup_search_tool()

        wiki_tool = AnalyzerTools.setup_wikipedia_tool()

        python_repl = AnalyzerTools.setup_python_repl_tool()

        notification_tool = AnalyzerTools.setup_notification_tool()

        all_tools = (
            browser_tools +
            file_tools +
            [search_tool, wiki_tool, python_repl, notification_tool]
        )

        return all_tools, browser, playwright
