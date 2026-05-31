from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
load_dotenv()

mcp = FastMCP("retail-communication")

# Store

inventory = {
    "niacinamide serum": 0,
    "vitamin c serum": 5,
    "retinol cream": 2,
}

restock_requests = {}


# Helper Functions

def normalize_product(product: str) -> str:
    """Standardize product names."""
    return product.strip().lower()


# MCP Tools

@mcp.tool()
def check_inventory(product: str) -> str:
    """
    Check if a product is in stock.
    """
    product = normalize_product(product)
    stock = inventory.get(product)

    if stock is None:
        return "Product not found."

    if stock == 0:
        return f"{product} is currently out of stock."

    return f"{product} is available. Quantity: {stock}"


@mcp.tool()
def request_restock_alert(product: str, customer: str) -> str:
    """
    Register a customer for restock notification.
    """
    product = normalize_product(product)

    if product not in restock_requests:
        restock_requests[product] = []

    if customer in restock_requests[product]:
        return f"{customer} is already subscribed for {product}."

    restock_requests[product].append(customer)

    return f"{customer} will be notified when {product} is restocked."


@mcp.tool()
def restock_product(product: str, quantity: int) -> str:
    """
    Add stock to a product.
    """
    product = normalize_product(product)

    if quantity <= 0:
        return "Quantity must be greater than 0."

    inventory[product] = inventory.get(product, 0) + quantity

    return f"{product} restocked successfully. New quantity: {inventory[product]}"


@mcp.tool()
def notify_customers(product: str) -> str:
    """
    Notify all customers waiting for a product.
    """
    product = normalize_product(product)

    customers = restock_requests.get(product, [])

    if not customers:
        return "No customers to notify."

    messages = []

    for customer in customers:
        messages.append(
            f"Notification sent to {customer}: {product} is now available!"
        )

    # Clear list after notification 
    restock_requests[product] = []

    return "\n".join(messages)


@mcp.tool()
def analyze_demand() -> str:
    """
    Analyze demand based on restock requests.
    """
    if not restock_requests:
        return "No demand data available."

    results = []

    for product, customers in restock_requests.items():
        results.append(
            f"{product}: {len(customers)} interested customers"
        )

    return "\n".join(results)

if __name__ == "__main__":
    mcp.run(transport="stdio")