from dotenv import load_dotenv
import os
import json
import datetime

load_dotenv(override=True)
sender_email = os.getenv("EMAIL")
password = os.getenv("APP_GMAIL_PASSWORD")
myself = os.getenv("TO_EMAIL")
in_memory_chat_history = {}
session_data = {
    "history": [],
    "email": "",
    "questions": [],
    "user_name": ""
}
def record_unkown_question(question, name="Name Not provided", email="not provide",  session_id=""):
    in_memory_chat_history[session_id]["email"] = email
    in_memory_chat_history[session_id]["name"] = name
    in_memory_chat_history[session_id]["questions"].append(question)
    return {"recorded":"ok"}

def store_email(email,session_id=""):
    in_memory_chat_history[session_id]["email"] = email
    return {"recorded":"ok"}

store_email_json = {
    "name": "store_email",
    "description": "Use this tool to store the email of any user who wants to stay in touch and has provided their email address.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The user's email address."
            }
        },
        "additionalProperties": False
    },
    "required": ["email"]
}

record_unkown_question_json = {
    "name": "record_unkown_question",
    "description": "Use this tool to record any question you couldn’t answer due to lack of information.",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The user's email address, if provided."
            },
            "name": {
                "type": "string",
                "description": "The user's name, if provided."
            },
            "question": {
                "type": "string",
                "description": "The unanswered question (or a short summary)."
            }
        },
        "additionalProperties": False
    },

    "required": ["question"]
}


def handle_tool_call( tool_calls, session_id=""): 
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        arguments["session_id"] = session_id
        print(f"Tool called: {tool_name}",flush=True)
        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
    return results

def chat(callback, chat_history, message, session_id):
    result = callback(message, chat_history,session_id)
    user_message_entry = {
        "role": "user",
        "content": message,
        "timestamp": str(datetime.datetime.now())
    }
    chat_history.append(user_message_entry)
    bot_message_entry = {
        "role": "assistant",
        "content": result,
        "timestamp": str(datetime.datetime.now())
    }
    chat_history.append(bot_message_entry)
    in_memory_chat_history[session_id]["history"] = chat_history
    return result