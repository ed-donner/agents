import os
from typing import Dict
import requests
from agents import Agent, function_tool



@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """
    Send an email with the given subject and HTML body using Mailgun API.
    
    Args:
        subject: Email subject line
        html_body: HTML content for the email body
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Mailgun configuration
        api_key = os.environ.get("MAILGUN_API_KEY")
        domain = os.environ.get("MAILGUN_DOMAIN", "sandboxfd631e04f8a941d5a5993a11227ea098.mailgun.org")
        from_email = os.environ.get("MAILGUN_FROM_EMAIL", f"Clinical Reports <mailgun@{domain}>")
        to_email = os.environ.get("EMAIL_ADDRESS", "dmitry756@gmail.com")
        
        if not api_key:
            return {
                "status": "error",
                "message": "MAILGUN_API_KEY environment variable not set"
            }
        
        # Mailgun API endpoint
        base_url = "https://api.mailgun.net"
        url = f"{base_url}/v3/{domain}/messages"
        
        # Prepare the email data
        data = {
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "html": html_body
        }
        
        # Send the request
        response = requests.post(
            url,
            auth=("api", api_key),
            data=data,
            timeout=10
        )
        
        response.raise_for_status()
        
        result = response.json()
        
        print(f"Email sent successfully. Mailgun ID: {result.get('id', 'N/A')}")
        
        return {
            "status": "success",
            "message": f"Email sent successfully to {to_email}",
            "mailgun_id": result.get("id", "N/A")
        }
        
    except requests.RequestException as e:
        error_msg = f"Mailgun API error: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail.get('message', '')}"
            except:
                error_msg += f" - HTTP {e.response.status_code}"
        
        print(f"Email error: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"Email error: {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }


INSTRUCTIONS = """You are an email delivery agent specialized in sending clinical and research reports.

You will be provided with HTML content for a clinical report. Your task is to:
1. Extract or create an appropriate subject line (or use the one provided)
2. Use the send_email tool to deliver the HTML report via Mailgun
3. Confirm successful delivery or report any errors

The HTML content is already formatted and ready to send. Do not modify the HTML structure.
If a subject line is not explicitly provided, use: "Pharmacogenomic Clinical Report - [Date]"
"""

email_agent = Agent(
    name="EmailAgent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
