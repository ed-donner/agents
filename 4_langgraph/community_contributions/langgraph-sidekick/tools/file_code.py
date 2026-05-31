from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_experimental.tools import PythonREPLTool


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()

async def file_code_tools():
    file_tools = get_file_tools()
    python_tool = PythonREPLTool()
    return file_tools + [python_tool]
