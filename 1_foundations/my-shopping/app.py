from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import json

load_dotenv(override=True)


store_inventory = {}
menu = {}

def stock_inventory(item, quantity):
    store_inventory[item] = store_inventory.get(item, 0) + quantity
    return report_store_inventory()

def take_from_store(item, quantity):
    if item not in store_inventory or store_inventory[item] < quantity:
        raise ValueError(f"Error: Insufficient quantity for '{item}'. "
                         f"Available: {store_inventory.get(item,0)}, Requested: {quantity}")
    store_inventory[item] -= quantity
    return report_store_inventory()


def add_menu_item(recipe_name, ingredients=[("item","quantity")]):
    menu[recipe_name] = ingredients
    return report_store_inventory()


def report_store_inventory():
    result = "Item (Quantity)\n"
    for key, value in store_inventory.items():
        result += f"{key} ({value})\n"
    return result


tools = [
    { 
        "type": "function",
        "function": {
            "name":"report_store_inventory",
            "description": "Use this tool to return a report to the owner on the state of the kitchen inventory.",
            "parameters": {},
            "additionalProperties": False
        }
    },
    { 
        "type": "function",
        "function": {
            "name":"stock_inventory",
            "description": "Use this tool to add items to the inventory. This can be used to stock the kitchen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "The name of the item or ingredient that you want to stock in the kitchen"
                    },
                    "quantity": {
                        "type": "number",
                        "description": "The amount of that item that you would like to add to the inventory"
                    }
                }
            },
            "required": ["item","quantity"],
            "additionalProperties": False
        }
    },
    { 
        "type": "function",
        "function": {
            "name":"take_from_store",
            "description": "Use this tool to take items from the inventory, so they can be used as ingredients for a recipe",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "The name of the item or ingredient that you want to remove from the kitchen"
                    },
                    "quantity": {
                        "type": "number",
                        "description": "The amount of that item that you would like to remove from the inventory"
                    }
                }
            },
            "required": ["item","quantity"],
            "additionalProperties": False
        }
    },
    { 
        "type": "function",
        "function": {
            "name":"add_menu_item",
            "description": "Use this tool to record the ingredients and their quantities required for a new menu item that the owner wants to add",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_name": {
                        "type": "string",
                        "description": "The name of the menu item or recipe"
                    },
                    "ingredients": {
                        "type": "object",
                        "description": "A list of tuples containing the various ingredients and their quantities that are required for the recipe."
                    }
                }
            },
            "required": ["item","quantity"],
            "additionalProperties": False
        }
    }
]

class Restaurant:

    def __init__(self):
        self.openai = OpenAI()

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            print(tool_name)
            arguments = json.loads(tool_call.function.arguments)
            tool = globals().get(tool_name)
            try:
                result = tool(**arguments) if tool else {}
            except ValueError as ve:
                result = {
                    "success": False,
                    "error": f"{ve}"
                }
            results.append({"role":"tool", "content": json.dumps(result), "tool_call_id": tool_call.id})
        return results

    def system_prompt(self):
        system_prompt = f"You are a Italian restaurant owner's assistant. Your responsibility is to manage the kitchen inventory. \
            You have a store of food ingredients that you stock on demand. \
            It is also your responsibility to help the owner identify ingredients needed to prepare a specific menu. \
            It is important that you keep track of the ingredients needed for a specific recipe on the menu. \
            This is because the special of the day is always (it is a must) one of the menu items. \
            When the owner tells you what the special for the day is you will immediately stock the kitchen inventory with all the ingredients required for that recipe. \
            The quantity for each ingredient will depend on the recipe for the special and how many plates of the special are expected to be served that day and accordingly. \
            Since the number of plates served every day varies, ask the owner before calculating quantities. \
            The owner can also ask you to serve a plate of the special. You should take whatever items you need from the inventory, if available and return the dish successfully made to the owner. \
            When any changes are made to the inventory please return a report to the owner."
        return system_prompt

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role":"user", "content":message}]
        # print(messages)
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)    
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content



if __name__ == "__main__":
    me = Restaurant()
    demo = gr.ChatInterface(me.chat, type="messages")
    demo.launch()
    