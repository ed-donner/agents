import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, function_tool, Runner
from ai_agents.database_manager_agent import DatabaseManagerAgent

load_dotenv(override=True)

@function_tool
async def sell_products(product: str, quantity: int):
    db_agent = DatabaseManagerAgent()

    # Have the db agent reduce the sold product by the quantity.
    sell_products_result = await db_agent.run_task(f"Sell product {product} with quantity {quantity}.")
    print(sell_products_result)

class ProductSalesAgent:
    def __init__(self):
        self.agent = Agent(
            name="Product Sales",
            instructions=(
                "You are a product sales agent."
                "You are given tools to perform the following tasks:"
                "- sell products, which reduces the quantity of a product by a specified quantity"
                "No additional output, the tools will print their own output."
                "Only make changes when asked explicitly."
            ),
            tools=[sell_products]
        )

    async def run_task(self, message: str):
        result = await Runner.run(self.agent, message)
        return result.final_output
    