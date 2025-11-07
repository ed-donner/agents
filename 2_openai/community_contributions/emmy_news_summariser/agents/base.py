"""Base agent class following OpenAI Agents SDK patterns."""

from typing import Any, Callable, List, Optional
from dataclasses import dataclass


def function_tool(func: Callable) -> Callable:
    """Decorator to mark a function as a tool for agents.
    
    This follows the OpenAI Agents SDK pattern for function tools.
    
    Args:
        func: Function to be decorated as a tool
        
    Returns:
        Decorated function with tool metadata
    """
    func._is_tool = True
    func._tool_name = func.__name__
    func._tool_description = func.__doc__ or ""
    return func


@dataclass
class Agent:
    """Agent class following OpenAI Agents SDK pattern.
    
    Example:
        Agent(
            name="Email agent",
            instructions="Send an email to the user",
            tools=[send_email],
            model="gemini-2.5-flash",
        )
    """
    name: str
    instructions: str
    tools: List[Callable]
    model: str = "gemini-2.5-flash"
    
    def __post_init__(self):
        """Validate tools after initialization."""
        for tool in self.tools:
            if not hasattr(tool, '_is_tool'):
                raise ValueError(
                    f"Tool {tool.__name__} must be decorated with @function_tool"
                )
    
    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', model='{self.model}')"
