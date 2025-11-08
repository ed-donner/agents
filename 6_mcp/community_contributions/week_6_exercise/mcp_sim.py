from datetime import datetime
import inspect
import asyncio

class MCPHost:
    def __init__(self, name="MCPHost"):
        self.name = name
        self.client = None
        print(f"[{self.name}] Host initialized at {datetime.now()}")

    def connect_client(self, client):
        self.client = client
        print(f"[{self.name}] Connected to MCP Client '{client.name}'")

    def request(self, tool_name, *args, **kwargs):
        if not self.client:
            raise RuntimeError(f"[{self.name}] No MCP Client connected.")
        print(f"[{self.name}] Requesting tool '{tool_name}' via client…")
        return self.client.execute(tool_name, *args, **kwargs)


class MCPClient:
    def __init__(self, name="LocalClient"):
        self.name = name
        self._tool_registry = {} 
        print(f"[{self.name}] Client initialized.")

    def register_tool(self, tool_callable):
        tool_name = getattr(tool_callable, "tool_name", None)
        if not tool_name:
            raise ValueError("missing tool name.")
        self._tool_registry[tool_name] = tool_callable
        print(f"[{self.name}] Registered tool: {tool_name}")

    def execute(self, tool_name, *args, **kwargs):
        tool = self._tool_registry.get(tool_name)
        if not tool:
            raise ValueError(f"[{self.name}] Tool '{tool_name}' not found.")
        print(f"[{self.name}] Routing request to tool '{tool_name}'")

        result = tool(*args, **kwargs)

        # corouting
        if inspect.isawaitable(result):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    return asyncio.run(result)
                else:
                    return loop.run_until_complete(result)
            except RuntimeError:
                return asyncio.run(result)

        return result
