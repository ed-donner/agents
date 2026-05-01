from contextlib import AsyncExitStack
from typing import Dict, List, Any
from agents.mcp import MCPServerStdio

class NikhilMCPManager:
    def __init__(self, config_map: Dict[str, dict]):
        self.config_map = config_map
        self.instances = {}
        self.exit_stack = AsyncExitStack()

    async def __aenter__(self):
        for key, conf in self.config_map.items():
            cache = conf.get('cache_tools_list', True)
            params = conf.get('params', {})
            instance = await self.exit_stack.enter_async_context(
                MCPServerStdio(params=params, cache_tools_list=cache)
            )
            self.instances[key] = instance
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.exit_stack.aclose()

    def __getattr__(self, key):
        if key in self.instances:
            return self.instances[key]
        raise AttributeError(f"No MCP instance named '{key}'")

    def all_instances(self) -> List:
        return list(self.instances.values())

    def get_instances(self, keys: List[str]) -> List:
        return [self.instances[k] for k in keys if k in self.instances]

    def as_dict(self) -> Dict[str, Any]:
        return self.instances.copy()
