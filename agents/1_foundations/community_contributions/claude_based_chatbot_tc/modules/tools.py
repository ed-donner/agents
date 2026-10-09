"""
Tool definitions and handlers for Claude
"""
import json
from .notification import push

# Tool functions that Claude can call
def record_user_details(email, name="Name not provided", notes="not provided"):
    """Record user contact information when they express interest"""
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    """Record questions that couldn't be answered"""
    push(f"Recording unknown question: {question}")
    return {"recorded": "ok"}

def search_faq(query):
    """Search the FAQ for a question or topic"""
    push(f"Searching FAQ for: {query}")
    return {"search_results": "ok"}

# Tool definitions in the format Claude expects
tool_schemas = [
    {
        "name": "record_user_details",
        "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "The email address of this user"},
                "name": {"type": "string", "description": "The user's name, if they provided it"},
                "notes": {"type": "string", "description": "Any additional context from the conversation"}
            },
            "required": ["email"]
        }
    },
    {
        "name": "record_unknown_question",
        "description": "Use this tool to record any question that couldn't be answered",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question that couldn't be answered"}
            },
            "required": ["question"]
        }
    },
    {
        "name": "search_faq",
        "description": "Searches a list of frequently asked questions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The user's question or topic to search for in the FAQ."}
            },
            "required": ["query"]
        }
    }
]

# Map of tool names to functions
tool_functions = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
    "search_faq": search_faq
}

def handle_tool_calls(tool_calls):
    """Process tool calls from Claude and execute the appropriate functions"""
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.name
        arguments = tool_call.input  # This is already a dict
        print(f"Tool called: {tool_name}", flush=True)
                
        # Get the function from tool_functions and call it with the arguments
        tool_func = tool_functions.get(tool_name)
        if tool_func:
            result = tool_func(**arguments)
        else:
            print(f"No function found for tool: {tool_name}")
            result = {"error": f"Tool {tool_name} not found"}
        
        # Format the result for Claude's response
        results.append({
            "role": "user", 
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": json.dumps(result)
                }
            ]
        })
    return results