from contextlib import AsyncExitStack
from typing import Dict, List, Any
from agents.mcp import MCPServerStdio

class MCPServers:
    def __init__(self, server_configs: Dict[str, dict]):
        """
        Create multiple MCP servers with different configurations.
        
        Args:
            server_configs: A dictionary mapping server names to their parameter dictionaries
        """
        self.server_configs = server_configs
        self.servers = {}
        self.stack = AsyncExitStack()
        
    async def __aenter__(self):
        """Set up all MCP servers and return self for attribute access."""
        for name, config in self.server_configs.items():
            # Use default cache_tools_list=True if not specified
            cache_tools = config.get('cache_tools_list', True)
            params = config.get('params', {})
            
            server = await self.stack.enter_async_context(
                MCPServerStdio(params=params, cache_tools_list=cache_tools)
            )
            self.servers[name] = server
            
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up all servers."""
        await self.stack.aclose()
        
    def __getattr__(self, name):
        """Allow attribute-style access to servers."""
        if name in self.servers:
            return self.servers[name]
        raise AttributeError(f"No server named '{name}'")
    
    def get_all_servers(self) -> List:
        """Return all MCP servers as a list."""
        return list(self.servers.values())
    
    def get_servers_by_names(self, names: List[str]) -> List:
        """Return specific MCP servers by their names."""
        return [self.servers[name] for name in names if name in self.servers]
    
    def get_server_dict(self) -> Dict[str, Any]:
        """Return the dictionary of all servers."""
        return self.servers.copy()
