"""
email_server.py - MCP Server for sending emails via Resend

A simple MCP server that wraps Resend's Email API.

Required Environment Variables:
- RESEND_API_KEY: Your Resend API key

Run with: uv run email_server.py

Get free Resend API key at: https://resend.com (100 emails/day free)

⚠️ FREE TIER LIMITATION:
   With free Resend, you can only send to YOUR OWN verified email address
   (the email you signed up with). To send to others, verify a custom domain.
"""
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from pathlib import Path
import resend
import os
import sys

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

mcp = FastMCP("email_server")

def log(msg: str):
    """Log to stderr for debugging."""
    print(f"[email_server] {msg}", file=sys.stderr)

# Log env loading on startup
if env_path:
    log(f"Loaded .env from: {env_path}")
log(f"RESEND_API_KEY present: {bool(os.getenv('RESEND_API_KEY'))}")


def init_resend():
    """Initialize Resend with API key."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise ValueError("RESEND_API_KEY must be set")
    resend.api_key = api_key


@mcp.tool()
async def send_email(
    to_email: str, 
    subject: str, 
    body: str, 
    from_email: str = "Shopping List <onboarding@resend.dev>"
) -> dict:
    """Send an email via Resend.
    
    Args:
        to_email: The recipient's email address
        subject: The email subject line
        body: The email body (plain text or HTML)
        from_email: The sender email (default: onboarding@resend.dev for testing)
    
    Returns:
        A dictionary with success status, email ID, and details.
    
    Note: With free Resend account, you can only send to your own verified email.
          To send to others, verify your domain at https://resend.com/domains
    """
    try:
        log(f"Attempting to send email to: {to_email}")
        init_resend()
        
        # Check if body looks like HTML
        is_html = body.strip().startswith('<') or '<br>' in body or '<p>' in body
        
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
        }
        
        if is_html:
            params["html"] = body
        else:
            # Convert plain text to simple HTML for better formatting
            html_body = body.replace('\n', '<br>')
            params["html"] = f"<div style='font-family: sans-serif;'>{html_body}</div>"
            params["text"] = body  # Also include plain text version
        
        log(f"Calling Resend API with params: to={to_email}, subject={subject}")
        email = resend.Emails.send(params)
        log(f"Resend response: {email}")
        
        return {
            "success": True,
            "email_id": email.get("id"),
            "to": to_email,
            "subject": subject,
            "message": f"Email sent successfully to {to_email}"
        }
        
    except Exception as e:
        error_msg = str(e)
        log(f"ERROR sending email: {error_msg}")
        
        # Provide helpful hints for common errors
        hints = ""
        error_lower = error_msg.lower()
        
        if "verify" in error_lower or "domain" in error_lower or "can only send" in error_lower:
            hints = "FREE TIER LIMIT: You can only send to your own verified email. To send to others, verify a domain at https://resend.com/domains"
        elif "validation" in error_lower or "invalid" in error_lower:
            hints = "FREE TIER LIMIT: The 'to' email must be the same as your Resend account email, or verify your own domain."
        elif "api" in error_lower or "key" in error_lower or "unauthorized" in error_lower:
            hints = "Check your RESEND_API_KEY is correct."
        elif "rate" in error_lower or "limit" in error_lower:
            hints = "Rate limited. Free tier allows 100 emails/day."
        else:
            hints = "Check Resend dashboard for details at https://resend.com/emails"
        
        log(f"Hint: {hints}")
        
        return {
            "success": False,
            "error": error_msg,
            "hint": hints,
            "to": to_email,
            "suggestion": "Try sending to your Resend account email, or verify your domain at https://resend.com/domains"
        }


@mcp.tool()
async def send_shopping_list_email(
    to_email: str,
    items: list,
    total_cost: float = None,
    budget: float = None,
    note: str = None
) -> dict:
    """Send a formatted shopping list via email.
    
    This is a convenience tool that formats the shopping list nicely.
    
    Args:
        to_email: The recipient's email address
        items: List of item dictionaries with name, quantity, category, price
        total_cost: Optional total cost of all items
        budget: Optional budget amount
        note: Optional personal note to include
    
    Returns:
        A dictionary with success status and details.
    """
    # Build HTML email
    html = """
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2d3748; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">
            🛒 Shopping List
        </h2>
    """
    
    if note:
        html += f'<p style="color: #4a5568; font-style: italic;">"{note}"</p>'
    
    html += '<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">'
    html += '''
        <tr style="background: #f7fafc;">
            <th style="text-align: left; padding: 10px; border-bottom: 1px solid #e2e8f0;">Item</th>
            <th style="text-align: center; padding: 10px; border-bottom: 1px solid #e2e8f0;">Qty</th>
            <th style="text-align: left; padding: 10px; border-bottom: 1px solid #e2e8f0;">Category</th>
            <th style="text-align: right; padding: 10px; border-bottom: 1px solid #e2e8f0;">Price</th>
        </tr>
    '''
    
    for item in items:
        name = item.get('name', 'Unknown')
        qty = item.get('quantity', 1)
        category = item.get('category', 'General')
        price = item.get('price')
        price_str = f"${price:.2f}" if price else "-"
        
        html += f'''
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{name}</td>
            <td style="text-align: center; padding: 10px; border-bottom: 1px solid #e2e8f0;">{qty}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; color: #718096;">{category}</td>
            <td style="text-align: right; padding: 10px; border-bottom: 1px solid #e2e8f0;">{price_str}</td>
        </tr>
        '''
    
    html += '</table>'
    
    # Add totals
    if total_cost is not None or budget is not None:
        html += '<div style="background: #f7fafc; padding: 15px; border-radius: 8px; margin-top: 20px;">'
        if total_cost is not None:
            html += f'<p style="margin: 5px 0;"><strong>Total:</strong> ${total_cost:.2f}</p>'
        if budget is not None:
            html += f'<p style="margin: 5px 0;"><strong>Budget:</strong> ${budget:.2f}</p>'
            if total_cost is not None:
                remaining = budget - total_cost
                color = "#48bb78" if remaining >= 0 else "#e53e3e"
                html += f'<p style="margin: 5px 0; color: {color};"><strong>Remaining:</strong> ${remaining:.2f}</p>'
        html += '</div>'
    
    html += '''
        <p style="color: #a0aec0; font-size: 12px; margin-top: 30px; text-align: center;">
            Sent from Shopping List Assistant 🛒
        </p>
    </div>
    '''
    
    # Send the email
    return await send_email(
        to_email=to_email,
        subject="🛒 Your Shopping List",
        body=html
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")

