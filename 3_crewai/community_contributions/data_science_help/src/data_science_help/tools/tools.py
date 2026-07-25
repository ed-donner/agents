import os
from crewai_tools import SerperDevTool, CodeInterpreterTool, JSONSearchTool, FileReadTool



def get_web_search_tool():
    if not os.getenv("SERPER_API_KEY"):
        raise RuntimeError("SERPER_API_KEY is not set. Please export it before running the crew.")
    return SerperDevTool(
        n_results=5,
        save_file=True,
        search_type="search",
    )

def get_code_interpreter_tool():
    return CodeInterpreterTool()

def get_json_search_tool():
    key = os.getenv("CHROMA_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if key and not os.getenv("CHROMA_OPENAI_API_KEY"):
        os.environ["CHROMA_OPENAI_API_KEY"] = key
    return JSONSearchTool()

def get_file_read_tool():
    return FileReadTool()