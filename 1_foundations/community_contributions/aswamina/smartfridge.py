from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import gradio as gr


load_dotenv(override=True)
openai = OpenAI()


# For pushover
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"


def push(message):
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)


def mark_complete(item: str):
    if item in groceries_inventory.keys():
        quantity = groceries_inventory[item]

        if quantity == 0:
            message = f"Please order {item} at this time\n"
            push(message)
            print(message)
    else:
        print("Item not found in the grocery list")


def update_groceries_status() -> str:
    remaining = {
        key: groceries_inventory[key] - groceries_consumed.get(key, 0)
        for key in groceries_inventory
    }

    result = ""
    for grocery, quantity in remaining.items():
        if quantity == 0:
            mark_complete(grocery)
            result += f"Grocery #{grocery}: {quantity}\n"
        else:
            result += f"Grocery #{grocery}: {quantity}\n"

    groceries_inventory.update(remaining)
    for key in remaining:
        groceries_consumed[key] = 0

    return result


def update_groceries_consumed(consumed: dict) -> str:
    result = ""
    for grocery, quantity in consumed.items():
        if grocery not in groceries_inventory:
            result += f"Item '{grocery}' not found in the grocery list.\n"
            continue
        if quantity < 0:
            result += f"Invalid quantity for Grocery #{grocery}: {quantity}\n"
            continue
        available = groceries_inventory[grocery] - groceries_consumed.get(grocery, 0)
        if quantity > available:
            result += (
                f"You cannot consume more {grocery} than what you have available.\n"
            )
            continue
        groceries_consumed[grocery] = groceries_consumed.get(grocery, 0) + quantity

    return result


def create_groceries_inventory(inventory: dict) -> str:
    groceries_inventory.update(inventory)
    return update_groceries_status()


create_groceries_inventory_json = {
    "name": "create_groceries_inventory",
    "description": 'Add new groceries and their quantities. Pass a single JSON object where each key is a grocery name (string) and each value is the quantity (integer). Example: {"eggs": 12, "milk": 1, "bread": 2}',
    "parameters": {
        "type": "object",
        "properties": {
            "inventory": {
                "type": "object",
                "description": 'Map of grocery item names to quantities (e.g. {"eggs": 12, "milk": 1}).',
                "additionalProperties": {"type": "integer"},
            }
        },
        "required": ["inventory"],
        "additionalProperties": False,
    },
}


mark_complete_json = {
    "name": "mark_complete",
    "description": "Mark the given grocery item as complete if its quantity is zero and return the full list",
    "parameters": {
        "type": "object",
        "properties": {
            "item": {
                "description": "The item to mark as complete. If the groceries_inventory of that item is zero, then it is time to order that item",
                "type": "string",
            }
        },
        "required": ["item"],
        "additionalProperties": False,
    },
}


updated_groceries_status_json = {
    "name": "update_groceries_status",
    "description": "Update the groceries inventory by subtracting consumed amounts, mark items with zero quantity as complete, and return the updated status",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}


update_groceries_consumed_json = {
    "name": "update_groceries_consumed",
    "description": 'Record groceries that have been consumed. Pass a JSON object where each key is a grocery name (string) and each value is the quantity consumed (integer). Example: {"eggs": 2, "bread": 1}',
    "parameters": {
        "type": "object",
        "properties": {
            "consumed": {
                "type": "object",
                "description": 'Map of grocery item names to quantities consumed (e.g. {"eggs": 2, "milk": 1}).',
                "additionalProperties": {"type": "integer"},
            }
        },
        "required": ["consumed"],
        "additionalProperties": False,
    },
}


tools = [
    {"type": "function", "function": create_groceries_inventory_json},
    {"type": "function", "function": mark_complete_json},
    {"type": "function", "function": updated_groceries_status_json},
    {"type": "function", "function": update_groceries_consumed_json},
]


def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        if tool_name == "create_groceries_inventory" and "inventory" not in arguments:
            arguments = {"inventory": arguments}
        if tool_name == "update_groceries_consumed" and "consumed" not in arguments:
            arguments = {"consumed": arguments}
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append(
            {
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id,
            }
        )
    return results


def loop(messages):
    done = False
    while not done:
        response = openai.chat.completions.create(
            model="gpt-5.2", messages=messages, tools=tools, reasoning_effort="none"
        )
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "tool_calls":
            message = response.choices[0].message
            tool_calls = message.tool_calls
            results = handle_tool_calls(tool_calls)
            messages.append(message)
            messages.extend(results)
        else:
            done = True
    return response.choices[0].message.content


system_message = """
You are a smart refrigerator assistant. You manage the user's grocery inventory and consumption.

**Interpreting the user:** Parse item names and quantities from natural or shorthand phrasing. All of these mean the same thing and should be interpreted as one item with a quantity:
- "I have 10 eggs" / "10 eggs" / "eggs 10" / "eggs: 10" → eggs: 10
- "I used 2 milk" / "milk 2" / "2 cups milk" → milk: 2 (use the number given; treat "cups" or "loaves" as the unit, quantity is the number)
Normalize item names to simple lowercase words (e.g. eggs, milk, bread, bananas) for tool calls. If the user says "I have 10 eggs" when setting up, pass {"eggs": 10}; if they say "eggs 10" when reporting consumption, pass {"eggs": 10} to update_groceries_consumed.

**Setup:** When the user gives a starting inventory (in any of the phrasings above), call create_groceries_inventory with a single object mapping item names to quantities (integers).

**When the user reports consumption:** Call update_groceries_consumed with an object of item names to quantities consumed (interpret "I used X", "X 3", "3 X", etc. as that item and quantity). Then call update_groceries_status.

**When any item's remaining quantity is zero:** Call mark_complete for that item so the user is notified to reorder it.

**Rules:** Use only the tools above; do not invent tools. If the user does not specify a quantity, infer a reasonable amount or use 0. Do not ask for clarification—use your tools and then respond with a clear summary or status.
"""

def chat(message, history):
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    result = loop(messages)
    return result


groceries_inventory = {}
groceries_consumed = {}
gr.ChatInterface(chat, type="messages", save_history=True).launch()


