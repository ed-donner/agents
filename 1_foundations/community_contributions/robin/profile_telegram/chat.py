
from dotenv import load_dotenv
from openai import AzureOpenAI
load_dotenv(override=True)
import os
from pypdf import PdfReader
import gradio as gr

if (os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_api_version") ):
    print("Azure OpenAI client initialized successfully.")
else:
    print("Environment variables for Azure OpenAI are not set properly.")


if (os.getenv("Telegram_TOKEN") and os.getenv("Telegram_CHAT_ID")):
    print("Telegram environment variables are set.")
else:
    print("Telegram environment variables are not set properly.")


def send_telegramMessage(message:str):
    import requests
    TOKEN = os.getenv("Telegram_TOKEN")
    CHAT_ID = os.getenv("Telegram_CHAT_ID")  # Replace with the real number you found
    TEXT = message
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': TEXT
    }
    response = requests.post(url, data=payload, verify=False)
    return response.status_code, response.json()


# test telegram message sending
# Uncomment the line below to test sending a message
# print(send_telegramMessage("Hello from Python!"))



###### Tools that AI will use
def record_user_details(email, name="Name not provided", notes="not provided"):
    send_telegramMessage(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    send_telegramMessage(f"Recording {question} asked that I couldn't answer")
    return {"recorded": "ok"}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]


# Not the best way of doing this, but it works, next code shown best way of doing this
# This function can take a list of tool calls, and run them. This is the IF statement!!
# def handle_tool_calls(tool_calls):
#     results = []
#     for tool_call in tool_calls:
#         tool_name = tool_call.function.name
#         arguments = json.loads(tool_call.function.arguments)
#         print(f"Tool called: {tool_name}", flush=True)

#         # THE BIG IF STATEMENT!!!
#         if tool_name == "record_user_details":
#             result = record_user_details(**arguments)
#         elif tool_name == "record_unknown_question":
#             result = record_unknown_question(**arguments)
#         results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
#     return results



class Me:

    def __init__(self):
        self.openai =  AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
        self.name = "Robin N"
        reader = PdfReader("./me/Profile.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("./me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    # This is a more elegant way that avoids the IF statement.
    def handle_tool_calls(self, tool_calls):
        import json
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
        particularly questions related to {self.name}'s career, background, skills and experience. \
        Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
        You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
        Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "
        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_calls(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()
