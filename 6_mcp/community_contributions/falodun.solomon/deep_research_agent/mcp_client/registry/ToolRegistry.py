class ToolRegistry:

    def __init__(self, clients):
        self.clients = clients
        self.tool_map = {}

    async def build(self):
        for client in self.clients:
            tools = await client.list_tools()

            for tool in tools:
                name = tool.name
                print(f"[ToolRegistry] Registering tool: {name}")
                self.tool_map[name] = client

    def get_client_for_tool(self, tool_name: str):
        return self.tool_map.get(tool_name)
    
