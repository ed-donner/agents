"""
MCP Server wrapper with retry logic and exponential backoff for rate-limited APIs.
"""

import asyncio
from typing import Any
from agents.mcp import MCPServerStdio
import os


class MCPServerStdioWithRetry(MCPServerStdio):
    """
    Wrapper around MCPServerStdio that adds retry logic with exponential backoff.
    """
    
    def __init__(self, *args, max_retries: int = None, initial_retry_delay: float = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.max_retries = max_retries or int(os.getenv("MCP_MAX_RETRIES", "3"))
        self.initial_retry_delay = initial_retry_delay or float(os.getenv("MCP_RETRY_DELAY", "2.0"))
    
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        Call MCP tool with retry logic.
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = await super().call_tool(tool_name, arguments)
                return result
            
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if "rate limit" in error_str or "429" in error_str:
                    last_error = e
                    
                    if attempt < self.max_retries:
                        # Calculate exponential backoff delay
                        delay = self.initial_retry_delay * (2 ** attempt)
                        
                        print(f"Rate limit hit for {tool_name}, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"Rate limit still exceeded after {self.max_retries} retries for {tool_name}")
                        raise
                else:
                    # Error, raise immediately
                    raise
        
        if last_error:
            raise last_error

