from __future__ import annotations

import ast
import operator
from datetime import datetime, timezone

from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain_core.tools import BaseTool, tool


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}


def _safe_math(expr: str) -> float:
    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = _eval(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        raise ValueError("Only numeric arithmetic expressions are allowed.")

    tree = ast.parse(expr, mode="eval")
    return _eval(tree)


@tool
def current_utc_time() -> str:
    """Return the current UTC date and time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression like '(12*8)/3 + 7'."""
    try:
        return str(_safe_math(expression))
    except Exception as exc:  # pragma: no cover - defensive path
        return f"Could not evaluate expression: {exc}"


def get_tools() -> list[BaseTool]:
    wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    return [current_utc_time, calculator, PythonREPLTool(), wiki_tool]
