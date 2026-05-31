import os, socket, requests
from agents import Agent, ModelSettings
from base_model import ollama_model
from dotenv import load_dotenv


load_dotenv(override=True)

telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
telegram_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
telegram_sync = False

try:
    print("Telegram DNS:", socket.gethostbyname_ex("api.telegram.org"))  # will raise if blocked
    telegram_sync = True
except:
    print("Telegram DNS blocked")

# @function_tool
def send_msg(query: str, concise_report: str) -> str:
    """Send a message to telegram using the original query and concise report"""

    def push(message):
        if telegram_sync:
            print(f"Push Sync: {message}")
            payload = {"chat_id": telegram_chat_id, "text": message}
            response = requests.post(telegram_url, json=payload)
            return response.json()
        else:
            print(f"Message not sent: {message}")
            return {"ok": True}

    r = push(f'Query: {query}\nDetails: {concise_report}')
    print("Msg response", r)
    return "done"


INSTRUCTIONS = """You are able to send a short and crisp telegram message based on a detailed report.
You will be provided with a detailed report. You should call your tool only once to request sending the message, 
converting the report into clean, well presented, short, and crisp message. """


def get_msg_agent(mcp_server):
    msg_agent = Agent(
        name="MessageAgent",
        instructions=INSTRUCTIONS,
        # tools=[send_msg],
        mcp_servers=[mcp_server],
        model=ollama_model,
        model_settings=ModelSettings(temperature=0),
    )
    return msg_agent
