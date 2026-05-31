from os import getenv
from typing import Optional
from twilio.rest import Client
from langchain.agents import Tool


def _twilio_client() -> Optional[Client]:
    sid = getenv("TWILIO_ACCOUNT_SID")
    token = getenv("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        return None
    return Client(sid, token)

def send_whatsapp(text: str) -> str:
    client = _twilio_client()
    if not client:
        raise RuntimeError("Twilio not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.")
    from_ = getenv("TWILIO_WHATSAPP_FROM")
    to = getenv("TWILIO_WHATSAPP_TO")
    if not from_ or not to:
        raise RuntimeError("TWILIO_WHATSAPP_FROM or TWILIO_WHATSAPP_TO not set.")
    msg = client.messages.create(
        body=text,
        from_=f"whatsapp:{from_}",
        to=f"whatsapp:{to}"
    )
    return msg.sid

whatsapp_tool = Tool(
    name="send_whatsapp",
    func=send_whatsapp,
    description="Send a WhatsApp message via Twilio (requires env variables)."
)
