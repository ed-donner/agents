from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
import ast
import operator
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper



load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

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
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


def _eval_math_expression(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operation: {op_type.__name__}")
        left = _eval_math_expression(node.left)
        right = _eval_math_expression(node.right)
        return SAFE_OPERATORS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operation: {op_type.__name__}")
        operand = _eval_math_expression(node.operand)
        return SAFE_OPERATORS[op_type](operand)
    raise ValueError("Only numeric arithmetic expressions are allowed.")


def calculate_expression(expression: str):
    """Safely evaluate a numeric arithmetic expression."""
    try:
        parsed = ast.parse(expression, mode="eval")
        result = _eval_math_expression(parsed.body)
    except Exception as exc:
        return f"Invalid expression: {exc}"
    return str(result)


async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    file_tools = get_file_tools()

    tool_search =Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    calc_tool = Tool(
        name="calculate_expression",
        func=calculate_expression,
        description="Use this tool to safely evaluate numeric arithmetic expressions. Example: (1200 * 1.15) - 320"
    )

    python_repl = PythonREPLTool()
    
    return file_tools + [push_tool, tool_search, python_repl, wiki_tool, calc_tool]

