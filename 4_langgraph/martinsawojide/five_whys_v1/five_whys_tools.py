import os

from dotenv import load_dotenv
from langchain.tools import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper, WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool

load_dotenv(override=True)


async def investigation_tools() -> list:
    """
    Build and return all tools available to the why_generator node.

    Returns a flat list of LangChain tools.  The Serper search tool is
    included only when SERPER_API_KEY is set; the agent falls back to
    LLM-only hypothesis generation when the key is absent.
    """
    tools: list = []

    # -- File I/O (sandboxed to the investigations/ directory) ---------------
    file_tools = FileManagementToolkit(root_dir="investigations").get_tools()
    tools.extend(file_tools)

    # -- Web search for known failure modes (optional) -----------------------
    serper_key = os.getenv("SERPER_API_KEY")
    if serper_key:
        serper = GoogleSerperAPIWrapper()
        tools.append(
            Tool(
                name="search_failure_modes",
                func=serper.run,
                description=(
                    "Search the web for known failure modes, root causes, and technical "
                    "information relevant to the current hypothesis or phenomenon. "
                    "Input should be a focused search query, e.g. "
                    "'hydraulic cylinder valve failure modes manufacturing'."
                ),
            )
        )

    # -- Wikipedia for technical term lookup ---------------------------------
    tools.append(
        WikipediaQueryRun(
            api_wrapper=WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=2000),
            description=(
                "Look up technical terminology, component descriptions, or process "
                "definitions. Use when you need to understand what a specific part or "
                "mechanism does before proposing hypotheses."
            ),
        )
    )

    # -- Python REPL for data / statistics analysis --------------------------
    tools.append(
        PythonREPLTool(
            description=(
                "Execute Python code to analyse sensor data, telemetry logs, or "
                "statistical patterns. Use pandas / numpy for data processing. "
                "Always print() your results so they appear in the tool output."
            )
        )
    )

    return tools
