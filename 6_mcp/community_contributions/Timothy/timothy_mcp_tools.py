"""
MCP Tool wrappers for Timothy agents.
Each tool exposes async methods for agent actions.
"""
from timothy_mcp import mcp_bus

class InventoryMCP:
    def __init__(self, agent):
        self.agent = agent

    async def get_inventory(self):
        return await mcp_bus.send("inventory/get", None)

    async def request_forecast(self, product, history):
        return await mcp_bus.send("inventory/request_forecast", {"product": product, "history": history})

class LogisticsMCP:
    def __init__(self, agent):
        self.agent = agent

    async def get_shipments(self):
        return await mcp_bus.send("logistics/get", None)

class DemandMCP:
    def __init__(self, agent):
        self.agent = agent

    async def forecast(self, product, history):
        return await mcp_bus.send("demand/forecast", {"product": product, "history": history})
