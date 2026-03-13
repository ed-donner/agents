"""
Tools for our Agents to use.
"""

from typing import Literal
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

load_dotenv(override=True)

class Tools:
    def __init__(self):
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_url = "https://api.pushover.net/1/messages.json"
        self.serper = GoogleSerperAPIWrapper()
        self.wiki = WikipediaAPIWrapper()
        self.tool_names = []
    
    def tools(self) -> list[Tool]:
        """
        Main entry point for retrieving and defining available tools.
        """
        return [
            self._serper_tool, 
            self._pushover_tool, 
            self._wikipedia_tool, 
            self._python_repl_tool, 
            self._file_tool
        ]
    
    def _serper_tool(self) -> Tool:
        """
        Serper tool - perform web searches.
        """
        return Tool (
            name="search",
            func=self.serper.run,
            description="Use this tool when you want to get the results of an online web search"
        )
    
    def _pushover_tool(self, text: str) -> Tool:
        """
        Pushover tool - ability to send push over texts to user.
        """
        def _pushover_function(self, text: str) -> Literal["success", "fail"]:
            """
            Sends pushover text to user.
            """
            try:
                requests.post(
                    self.pushover_url, 
                    data = {"token": self.pushover_token, "user": self.pushover_user, "message": text}
                )
                return "success"
            except Exception as e:
                print(f"Error processing pushover tool: {e}")
                return "fail"
        
        return Tool (
            name="push",
            func=_pushover_function,
            description="Use this tool when you want to send a push notification"
        )
    
    def _wikipedia_tool(self) -> Tool:
        """
        Wikipedia tool - performing wiki searches.
        """
        return WikipediaQueryRun(api_wrapper=self.wiki)
    
    def _python_repl_tool(self) -> Tool:
        """
        Python repl tool - writing/running Python code.
        """
        return PythonREPLTool()
    
    def _file_tool(self, root_dir: str = "sandbox") -> Tool:
        """
        File tool - interacting with file explorer.
        """
        return FileManagementToolkit(root_dir=root_dir)