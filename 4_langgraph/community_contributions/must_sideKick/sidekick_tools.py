from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import Tool
from dotenv import load_dotenv
import os

load_dotenv(override=True)

serper = GoogleSerperAPIWrapper() if os.getenv("SERPER_API_KEY") else None

def get_file_tools():
    sandbox_dir = os.path.join(os.path.dirname(__file__), "sandbox")
    os.makedirs(sandbox_dir, exist_ok=True)
    toolkit = FileManagementToolkit(root_dir=sandbox_dir)
    return toolkit.get_tools()

def get_tools():
    tools = get_file_tools()
    
    if serper:
        tools.append(Tool(
            name="search",
            func=serper.run,
            description="Use this tool when you want to get the results of an online web search"
        ))
        
    tools.append(WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()))
    tools.append(PythonREPLTool())
    
    return tools
