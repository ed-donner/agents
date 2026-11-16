from agents import function_tool
from bot import send_telegram_message


@function_tool
async def send_message(message: str) -> str:
    """Send message to a customer in telegram"""
    await send_telegram_message(message)
    return "Message sent"
