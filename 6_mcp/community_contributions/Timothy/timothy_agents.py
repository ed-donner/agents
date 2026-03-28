"""
Agent and resource models for the supply chain platform.
"""
import pandas as pd
import asyncio
from timothy_db import get_inventory, get_shipments, get_forecast
from timothy_llm import query_llm
from timothy_mcp import mcp_bus
import logging

def create_agents():
    """Create and return all supply chain agents as a dict."""
    inventory = InventoryManager()
    logistics = LogisticsCoordinator()
    demand = DemandForecaster()
    return {"inventory": inventory, "logistics": logistics, "demand": demand}


class InventoryManager:
    """Agent responsible for inventory management."""
    def __init__(self):
        @mcp_bus.tool("inventory/get")
        async def handle_get_inventory(message):
            data = get_inventory()
            return data
        self.handle_get_inventory = handle_get_inventory

        @mcp_bus.tool("inventory/request_forecast")
        async def handle_request_forecast(message):
            forecast = await mcp_bus.send("demand/forecast", message)
            return forecast
        self.handle_request_forecast = handle_request_forecast

    def get_inventory_table(self):
        try:
            data = asyncio.run(self.handle_get_inventory(None))
            return pd.DataFrame(data)
        except Exception as e:
            logging.error(f"InventoryManager error: {e}")
            return pd.DataFrame([{"Product": "Error", "Stock": 0, "Location": str(e)}])

class LogisticsCoordinator:
    """Agent responsible for logistics coordination."""
    def __init__(self):
        @mcp_bus.tool("logistics/get")
        async def handle_get_shipments(message):
            data = get_shipments()
            return data
        self.handle_get_shipments = handle_get_shipments

    def get_shipments_table(self):
        try:
            data = asyncio.run(self.handle_get_shipments(None))
            return pd.DataFrame(data)
        except Exception as e:
            logging.error(f"LogisticsCoordinator error: {e}")
            return pd.DataFrame([{"ShipmentID": 0, "Product": "Error", "Status": str(e)}])

class DemandForecaster:
    """Agent responsible for demand forecasting using LLM."""
    def __init__(self):
        @mcp_bus.tool("demand/forecast")
        async def handle_forecast(message):
            product = message.get("product")
            history = message.get("history", [])
            prompt = f"Forecast demand for {product} given this history: {history}"
            result = query_llm(prompt)
            return {"Product": product, "Forecast": result}
        self.handle_forecast = handle_forecast

        @mcp_bus.tool("demand/get_forecast")
        async def handle_get_forecast(message):
            data = get_forecast()
            return data
        self.handle_get_forecast = handle_get_forecast

    def get_forecast_table(self):
        try:
            data = asyncio.run(self.handle_get_forecast(None))
            return pd.DataFrame(data)
        except Exception as e:
            logging.error(f"DemandForecaster error: {e}")
            return pd.DataFrame([{"Product": "Error", "Forecast": str(e)}])

    def forecast_demand(self, product, history):
        try:
            result = asyncio.run(mcp_bus.send("demand/forecast", {"product": product, "history": history}))
            return result
        except Exception as e:
            logging.error(f"LLM forecast error: {e}")
            return f"LLM error: {e}"
