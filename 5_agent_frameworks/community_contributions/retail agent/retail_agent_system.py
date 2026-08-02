import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# Story (for context)
# =========================
STORY = """
Whenever I walk into my favorite skincare store, there’s always that one product I’m looking for.
I already know where it sits on the shelf. I go straight to it without even thinking.

And then… it’s not there.

I ask the attendant:
“It’s out of stock… but we can take your number and let you know when it’s back.”

Days pass. Weeks pass. No one calls.

The problem isn’t care — it’s the lack of a system.

This project fixes that.
"""

class RetailAgent:
    def __init__(self, name):
        self.name = name

    def respond(self, message):
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a helpful retail assistant."},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content



inventory = {
    "niacinamide serum": 0,
    "vitamin c serum": 5,
    "retinol cream": 2
}

def check_inventory(product):
    product = product.lower()
    stock = inventory.get(product)

    if stock is None:
        return "Product not found"
    elif stock == 0:
        return "Out of stock"
    return f"In stock: {stock}"



class SmartRetailAgent:
    def handle_request(self, product, customer_name):
        stock_status = check_inventory(product)

        if stock_status == "Out of stock":
            return f"{product} is out of stock. Would you like to be notified?"

        return f"{product} is available. {stock_status}"



restock_requests = {}

def request_notification(product, customer):
    if product not in restock_requests:
        restock_requests[product] = []

    restock_requests[product].append(customer)
    return f"{customer} will be notified when {product} is restocked."


def notify_users(product):
    print("\nSending notifications...")
    for user in restock_requests.get(product, []):
        print(f"Notification sent to {user}: {product} is now available!")



def analyze_demand():
    print("\nDemand Analysis:")
    if not restock_requests:
        print("No demand data yet.")
        return

    for product, users in restock_requests.items():
        print(f"{product}: {len(users)} interested customers")



def main():
    print("\n=== STORY CONTEXT ===")
    print(STORY)

    agent = SmartRetailAgent()
    product = "niacinamide serum"

    print("\n=== STEP 1: Customer Request ===")
    response = agent.handle_request(product, "Mugao")
    print(response)

    print("\n=== STEP 2: Customer Subscribes ===")
    print(request_notification(product, "Mugao"))
    print(request_notification(product, "Alice"))

    print("\n=== STEP 3: Restock Product ===")
    inventory[product] = 10
    print("Product restocked.")

    print("\n=== STEP 4: Notify Customers ===")
    notify_users(product)

    print("\n=== STEP 5: Demand Insights ===")
    analyze_demand()


if __name__ == "__main__":
    main()