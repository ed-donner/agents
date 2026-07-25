from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Memory Server")

memory = {}

@mcp.tool()
def store_memory(user_id: str, key: str, value: str):
    memory.setdefault(user_id, {})[key] = value
    return "stored"

@mcp.tool()
def get_memory(user_id: str):
    return memory.get(user_id, {})

if __name__ == "__main__":
    mcp.run()