"""
sms_server.py - MCP Server for sending SMS via Email-to-SMS Gateway

A FREE SMS solution that uses carrier email gateways to send text messages.
No Twilio account or API keys needed!

How it works:
- Most carriers have email addresses that deliver as SMS
- Example: 5551234567@txt.att.net sends SMS to that AT&T number

Required Environment Variables:
- RESEND_API_KEY: Your Resend API key (for sending the email)

Supported Carriers (US):
- AT&T, Verizon, T-Mobile, Sprint, Cricket, Metro PCS, US Cellular, Boost, Virgin

Run with: uv run sms_server.py
"""
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from pathlib import Path
import resend
import os
import re

# Load environment variables - search up to project root
def find_and_load_dotenv():
    """Find .env file by searching up the directory tree."""
    current = Path(__file__).resolve().parent
    for _ in range(10):  # Search up to 10 levels
        env_file = current / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
            return str(env_file)
        current = current.parent
    # Fallback to default behavior
    load_dotenv(override=True)
    return None

env_path = find_and_load_dotenv()

mcp = FastMCP("sms_server")

# Email-to-SMS Gateway addresses by carrier
CARRIER_GATEWAYS = {
    # Major US carriers
    "att": "txt.att.net",
    "at&t": "txt.att.net",
    "verizon": "vtext.com",
    "tmobile": "tmomail.net",
    "t-mobile": "tmomail.net",
    "sprint": "messaging.sprintpcs.com",
    
    # Prepaid / MVNOs
    "cricket": "sms.cricketwireless.net",
    "metro": "mymetropcs.com",
    "metropcs": "mymetropcs.com",
    "boost": "sms.myboostmobile.com",
    "virgin": "vmobl.com",
    "uscellular": "email.uscc.net",
    "us cellular": "email.uscc.net",
    "republic": "text.republicwireless.com",
    "googlefi": "msg.fi.google.com",
    "google fi": "msg.fi.google.com",
    "fi": "msg.fi.google.com",
    "xfinity": "vtext.com",  # Uses Verizon network
    "visible": "vtext.com",  # Uses Verizon network
    "mint": "tmomail.net",   # Uses T-Mobile network
    "mint mobile": "tmomail.net",
}


def init_resend():
    """Initialize Resend with API key."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise ValueError("RESEND_API_KEY must be set")
    resend.api_key = api_key


def clean_phone_number(phone: str) -> str:
    """Clean phone number to digits only."""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Remove country code if present
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    return digits


def get_sms_email(phone: str, carrier: str) -> str:
    """Get the email address for SMS gateway."""
    clean_phone = clean_phone_number(phone)
    carrier_lower = carrier.lower().strip()
    
    gateway = CARRIER_GATEWAYS.get(carrier_lower)
    if not gateway:
        raise ValueError(f"Unknown carrier: {carrier}. Supported: {', '.join(sorted(set(CARRIER_GATEWAYS.keys())))}")
    
    return f"{clean_phone}@{gateway}"


@mcp.tool()
async def send_sms(phone_number: str, carrier: str, message: str) -> dict:
    """Send an SMS message via email-to-SMS gateway (FREE!).
    
    Args:
        phone_number: The recipient's phone number (e.g., "555-123-4567" or "5551234567")
        carrier: The mobile carrier (att, verizon, tmobile, sprint, cricket, metro, boost, virgin, mint, googlefi)
        message: The text message to send (keep under 160 chars for best results)
    
    Returns:
        A dictionary with success status and details.
    
    Note: This uses email-to-SMS gateways which are FREE but may have slight delays.
    """
    try:
        init_resend()
        
        # Build the SMS email address
        sms_email = get_sms_email(phone_number, carrier)
        
        # SMS should be plain text, no HTML
        # Keep it short - SMS has 160 char limit per segment
        if len(message) > 160:
            message = message[:157] + "..."
        
        # Send via Resend
        email = resend.Emails.send({
            "from": "Shopping List <onboarding@resend.dev>",
            "to": [sms_email],
            "subject": "",  # SMS doesn't use subject
            "text": message,
        })
        
        return {
            "success": True,
            "email_id": email.get("id"),
            "to_phone": phone_number,
            "carrier": carrier,
            "gateway_email": sms_email,
            "message": f"SMS sent to {phone_number} via {carrier} gateway",
            "note": "Message may take 1-2 minutes to arrive"
        }
        
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "to_phone": phone_number,
            "hint": "Make sure the carrier name is correct (att, verizon, tmobile, etc.)"
        }
    except Exception as e:
        error_msg = str(e)
        return {
            "success": False,
            "error": error_msg,
            "to_phone": phone_number
        }


@mcp.tool()
async def list_supported_carriers() -> dict:
    """List all supported mobile carriers for SMS.
    
    Returns:
        A dictionary with carrier names and their gateway domains.
    """
    # Group by actual gateway to show which are the same
    unique_carriers = {}
    for carrier, gateway in sorted(CARRIER_GATEWAYS.items()):
        if gateway not in unique_carriers:
            unique_carriers[gateway] = []
        unique_carriers[gateway].append(carrier)
    
    return {
        "success": True,
        "carriers": list(set(CARRIER_GATEWAYS.keys())),
        "common_carriers": ["att", "verizon", "tmobile", "sprint", "cricket", "metro", "mint", "googlefi"],
        "note": "Use the carrier name when calling send_sms (e.g., carrier='verizon')"
    }


@mcp.tool()
async def send_shopping_list_sms(
    phone_number: str,
    carrier: str,
    items: list,
    total_cost: float = None
) -> dict:
    """Send a formatted shopping list via SMS.
    
    This formats the list concisely for SMS (160 char limit per message).
    
    Args:
        phone_number: The recipient's phone number
        carrier: The mobile carrier (att, verizon, tmobile, etc.)
        items: List of item dictionaries with name and quantity
        total_cost: Optional total cost
    
    Returns:
        A dictionary with success status and details.
    """
    # Build concise SMS message
    lines = []
    for item in items[:10]:  # Limit to 10 items for SMS
        name = item.get('name', '?')
        qty = item.get('quantity', 1)
        if qty > 1:
            lines.append(f"{name} x{qty}")
        else:
            lines.append(name)
    
    message = "Shopping: " + ", ".join(lines)
    
    if total_cost:
        message += f" (${total_cost:.2f})"
    
    if len(items) > 10:
        message += f" +{len(items)-10} more"
    
    return await send_sms(phone_number, carrier, message)


if __name__ == "__main__":
    mcp.run(transport="stdio")
