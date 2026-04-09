class Executor:

    def __init__(self, registry):
        self.registry = registry

    async def execute(self, action: dict):
        tool = action["tool"]
        payload = action["input"]

        client = self.registry.get_client_for_tool(tool)

        if not client:
            raise ValueError(f"No MCP server found for tool: {tool}")

        print(f"\n[EXECUTOR] Calling tool: {tool}")
        print(f"[EXECUTOR] Payload: {payload}")

        result = await client.invoke(tool, payload)

        print(f"[EXECUTOR] Raw Result: {result}\n")

        return result