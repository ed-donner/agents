"""
AI-Powered Supply Chain Optimization Platform (Minimal Version)
- Multi-agent, modular, and data-driven.
- Agents: InventoryManager, LogisticsCoordinator, DemandForecaster
- Uses OpenRouter for LLM access
- Simple SQLite persistence
- Gradio dashboard for monitoring
"""




import gradio as gr
import logging
from dotenv import load_dotenv
from timothy_agents import InventoryManager, LogisticsCoordinator, DemandForecaster
from timothy_db import get_inventory, get_shipments, get_forecast

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


# Instantiate agents (registers with MCP bus)
inventory_agent = InventoryManager()
logistics_agent = LogisticsCoordinator()
demand_agent = DemandForecaster()

# UI functions

def show_inventory():
    import asyncio
    df = inventory_agent.get_inventory_table()
    # Add forecast as a new column for Widget A
    try:
        forecast = asyncio.run(
            inventory_agent.handle_request_forecast({"product": "Widget A", "history": [120, 130, 125]})
        )
    except Exception as e:
        forecast = {"Forecast": f"Error: {e}"}
    if isinstance(forecast, dict) and "Forecast" in forecast:
        df.loc[df["Product"] == "Widget A", "Forecast"] = forecast["Forecast"]
    return df

def inventory_details(product):
    # Show details and allow user to request a new forecast
    import asyncio
    df = inventory_agent.get_inventory_table()
    product_row = df[df["Product"] == product]
    if product_row.empty:
        return f"No data for {product}"
    history = [int(product_row.iloc[0]["Stock"])] * 3  # Example: use current stock as history
    forecast = asyncio.run(inventory_agent.handle_request_forecast({"product": product, "history": history}))
    return f"Product: {product}\nCurrent Stock: {product_row.iloc[0]['Stock']}\nLocation: {product_row.iloc[0]['Location']}\nForecast: {forecast.get('Forecast', 'N/A')}"

def show_shipments():
    return logistics_agent.get_shipments_table()

def show_forecast():
    return demand_agent.get_forecast_table()


def main_ui():
    with gr.Blocks(title="Supply Chain Dashboard") as ui:
        gr.Markdown("# Supply Chain Optimization Platform")
        gr.Markdown(
            """
            **Production Version**  
            - Secure API keys in .env  
            - Real database access  
            - Error handling and logging enabled  
            - Modular agent architecture  
            """
        )
        with gr.Tab("Inventory"):
            gr.Dataframe(show_inventory, label="Current Inventory", interactive=False)
            gr.Markdown("Select a product to view details and request a new forecast:")
            product_list = [row["Product"] for row in get_inventory()]
            product_dropdown = gr.Dropdown(choices=product_list, label="Product", value=product_list[0] if product_list else None)
            details_output = gr.Textbox(label="Product Details")
            product_dropdown.change(fn=inventory_details, inputs=product_dropdown, outputs=details_output)
        with gr.Tab("Logistics"):
            gr.Dataframe(show_shipments, label="Shipments", interactive=False)
        with gr.Tab("Demand Forecast"):
            gr.Dataframe(show_forecast, label="Forecast", interactive=False)
    return ui

if __name__ == "__main__":
    ui = main_ui()
    ui.launch(inbrowser=True)
