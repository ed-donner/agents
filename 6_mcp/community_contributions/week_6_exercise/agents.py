from functools import wraps
from datetime import datetime
import inspect
import asyncio

class Agent:
    def __init__(self, name, instructions="", model=None, tools=None, mcp_servers=None):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools or []
        self.mcp_servers = mcp_servers

    def as_tool(self, tool_name: str, tool_description: str, func=None):
        async def async_wrapper(*args, **kwargs):
            print(f"[Agent Tool] '{tool_name}' called by {self.name} at {datetime.now()}")

            if func is None:
                return None
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result

        # Ametadata
        async_wrapper.tool_name = tool_name
        async_wrapper.tool_description = tool_description

        # Store tool
        self.tools.append(async_wrapper)

        return async_wrapper

    def run(self, *args, **kwargs):
        """Default run method (sync)."""
        print(f"[Agent] '{self.name}' running at {datetime.now()} with args={args}, kwargs={kwargs}")
        return None



class Tool:
    def __init__(self, func):
        wraps(func)(self)
        self.func = func
        self.func.tool_name = getattr(func, "tool_name", func.__name__)
        self.func.tool_description = getattr(func, "tool_description", "")

    async def __call__(self, *args, **kwargs):
        print(f"[Tool] '{self.func.__name__}' called at {datetime.now()}")

        result = self.func(*args, **kwargs)

        # corouting
        if inspect.isawaitable(result):
            return await result
        return result
