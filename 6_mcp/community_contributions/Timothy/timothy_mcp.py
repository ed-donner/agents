"""
MCP (Multi-Agent Communication Protocol) for Timothy project.
Implements an async in-process message bus for agent-to-agent communication.
"""
import asyncio
from typing import Callable, Dict, Any

class MCPBus:
    def __init__(self):
        self.handlers: Dict[str, Callable[[Any], Any]] = {}

    def register(self, topic: str, handler: Callable[[Any], Any]):
        self.handlers[topic] = handler

    async def send(self, topic: str, message: Any) -> Any:
        if topic in self.handlers:
            if asyncio.iscoroutinefunction(self.handlers[topic]):
                return await self.handlers[topic](message)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.handlers[topic], message)
        else:
            raise ValueError(f"No handler registered for topic: {topic}")

    def tool(self, topic: str):
        """Decorator to register a function as an MCP tool."""
        def decorator(func):
            self.register(topic, func)
            return func
        return decorator

# Singleton bus for the app
mcp_bus = MCPBus()
