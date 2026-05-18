"""
Orchestrator for Timothy Supply Chain Agents.
Periodically coordinates agent actions using async and MCP bus.
"""
import asyncio
import os
from dotenv import load_dotenv
from timothy_agents import create_agents
from timothy_mcp_tools import InventoryMCP, LogisticsMCP, DemandMCP

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))

async def run_every_n_minutes():
    agents = create_agents()
    inventory_mcp = InventoryMCP(agents["inventory"])
    logistics_mcp = LogisticsMCP(agents["logistics"])
    demand_mcp = DemandMCP(agents["demand"])
    while True:
        # Example: Inventory agent requests a forecast from Demand agent
        forecast = await inventory_mcp.request_forecast("Widget A", [120, 130, 125])
        print(f"Forecast for Widget A: {forecast}")
        # Example: Logistics agent gets shipments
        shipments = await logistics_mcp.get_shipments()
        print(f"Shipments: {shipments}")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)

if __name__ == "__main__":
    print(f"Starting orchestrator to run every {RUN_EVERY_N_MINUTES} minutes")
    asyncio.run(run_every_n_minutes())
