"""
Tool Collection for Sidekick AI Assistant

Tool Categories:
1. Web Browsing: Playwright for browser automation
2. Search: Tavily, Google Serper, DuckDuckGo
3. Research: Wikipedia, ArXiv (academic papers)
4. Code Execution: Python REPL
5. File Management: Read/write files in sandbox
6. Notifications: Push notifications via 7. LLM Tools: Summarization, translation
"""

from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain_core.tools import Tool, StructuredTool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
# from langchain_community.tools.arxiv.tool import ArxivQueryRun
# from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper, ArxivAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

load_dotenv(override=True)

# Configuration
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

# Initialize search wrappers
serper = GoogleSerperAPIWrapper()

async def playwright_tools():
    """
    Initialize Playwright browser automation tools.
    
    Provides tools for:
    - Navigating to URLs
    - Clicking elements
    - Extracting text from pages
    - Filling forms
    
    Returns:
        Tuple of (tools_list, browser_instance, playwright_instance)
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright

def push(text: str):
    """
    Send a push notification to the user via Pushover.
    
    Useful for alerting the user about completed tasks or important updates.
    
    Args:
        text: The notification message to send
        
    Returns:
        str: "success" if notification was sent
    """
    try:
        requests.post(
            pushover_url, 
            data={
                "token": pushover_token, 
                "user": pushover_user, 
                "message": text
            }
        )
        return "success"
    except Exception as e:
        return f"Failed to send notification: {str(e)}"


def get_file_tools():
    """
    Get tools for file operations (read, write, list) in the sandbox directory.
    
    Security: All file operations are restricted to the 'sandbox' folder.
    
    Returns:
        List of file management tools
    """
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


class SummarizeInput(BaseModel):
    """Input schema for text summarization"""
    text: str = Field(description="The text to summarize")
    max_length: Optional[int] = Field(
        default=200, 
        description="Maximum length of summary in words"
    )


class TranslateInput(BaseModel):
    """Input schema for text translation"""
    text: str = Field(description="The text to translate")
    target_language: str = Field(description="Target language (e.g., 'Spanish', 'French')")


def create_llm_tools():
    """
    Create specialized LLM-powered tools for advanced text processing.
    
    Tools:
    1. smart_summarizer: Intelligent text summarization
    2. translator: Multi-language translation
    
    Returns:
        List of LLM-powered tools
    """
    llm = ChatOpenAI(model="nvidia/nemotron-3-nano-30b-a3b:free",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",)
    
    def summarize_text(text: str, max_length: int = 200) -> str:
        """
        Intelligently summarize long text while preserving key information.
        
        Args:
            text: Text to summarize
            max_length: Maximum words in summary
            
        Returns:
            Concise summary of the text
        """
        prompt = f"""Summarize the following text in no more than {max_length} words. 
        Focus on the most important information:

        {text}

        Summary:"""
        response = llm.invoke([{"role": "user", "content": prompt}])
        return response.content
    
    def translate_text(text: str, target_language: str) -> str:
        """
        Translate text to another language while preserving meaning and tone.
        
        Args:
            text: Text to translate
            target_language: Target language name
            
        Returns:
            Translated text
        """
        prompt = f"""Translate the following text to {target_language}. 
        Preserve the tone and meaning:

        {text}

        Translation:"""
        response = llm.invoke([{"role": "user", "content": prompt}])
        return response.content
    
    summarizer = StructuredTool.from_function(
        func=summarize_text,
        name="smart_summarizer",
        description="Summarize long text intelligently, preserving key information. Use this when you need to condense articles, documents, or web pages.",
        args_schema=SummarizeInput
    )
    
    translator = StructuredTool.from_function(
        func=translate_text,
        name="translator",
        description="Translate text to any language while preserving meaning and tone",
        args_schema=TranslateInput
    )
    
    return [summarizer, translator]


async def other_tools():
    """
    Gather all non-browser tools available to the assistant.
    
    Tool Categories:
    - Notifications: Push alerts
    - File Operations: Read/write files
    - Web Search: Google, Tavily, DuckDuckGo
    - Research: Wikipedia, ArXiv (academic papers)
    - Code: Python REPL
    - LLM Tools: Summarization, translation
    
    Returns:
        List of all available tools
    """
    # Notification tool
    push_tool = Tool(
        name="send_push_notification", 
        func=push, 
        description="Send a push notification to the user. Use when task is complete or urgent alert is needed."
    )
    
    # File management tools
    file_tools = get_file_tools()
    
    # Search tools
    tool_search = Tool(
        name="google_search",
        func=serper.run,
        description="Search Google for current information, news, and general queries. Returns top results with snippets."
    )
    
    # DuckDuckGo - privacy-focused alternative search
    # ddg_search = DuckDuckGoSearchRun()
    
    # Tavily - AI-optimized search
    tavily_tool = TavilySearchResults(
        max_results=5,
        description="AI-optimized search that returns highly relevant results. Best for research and fact-finding."
    )
    
    # Wikipedia - encyclopedia knowledge
    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(
        api_wrapper=wikipedia,
        description="Search Wikipedia for encyclopedic knowledge, definitions, and background information."
    )
    
    # ArXiv - academic papers and research
    # arxiv = ArxivAPIWrapper()
    # arxiv_tool = ArxivQueryRun(
    #     api_wrapper=arxiv,
    #     description="Search ArXiv for academic papers, research, and scientific publications. Use for technical or scientific queries."
    # )
    
    # Python REPL - code execution
    python_repl = PythonREPLTool()
    python_repl.description = """Execute Python code to perform calculations, data processing, or analysis. 
    IMPORTANT: Use print() to see output. The code runs in an isolated environment."""
    
    # LLM-powered tools
    llm_tools = create_llm_tools()
    
    # Combine all tools
    all_tools = (
        file_tools + 
        [push_tool, tool_search, tavily_tool] +
        [wiki_tool] +
        [python_repl] +
        llm_tools
    )
    
    return all_tools


