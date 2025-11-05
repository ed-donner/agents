import os
import re
from typing import Dict
import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool


@function_tool
def send_email(recipient_email: str, subject: str, html_body: str) -> Dict[str, str]:
    """
    Send an email with the given subject and HTML body to the specified recipient
    
    Args:
        recipient_email: Email address of the recipient
        subject: Subject line for the email
        html_body: HTML formatted email body
        
    Returns:
        Dict with status information
    """
    try:
        # Validate environment variable
        api_key = os.environ.get("SENDGRID_API_KEY")
        if not api_key:
            print("Error: SENDGRID_API_KEY not found in environment variables")
            return {"status": "error", "message": "SendGrid API key not configured"}
        
        # Validate sender email
        sender_email = os.environ.get("SENDGRID_SENDER_EMAIL", "noreply@deepresearch.ai")
        
        # Initialize SendGrid client
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        
        # Create email
        from_email = Email(sender_email)
        to_email = To(recipient_email)
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()
        
        # Send email
        response = sg.client.mail.send.post(request_body=mail)
        
        print(f"Email sent successfully! Status code: {response.status_code}")
        print(f"Recipient: {recipient_email}")
        
        return {
            "status": "success",
            "message": f"Email sent successfully to {recipient_email}",
            "status_code": response.status_code
        }
        
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(f"Error: {error_msg}")
        return {"status": "error", "message": error_msg}


INSTRUCTIONS = """You are an email composition specialist for a research service.

Your task:
1. Receive a research report and the recipient's email address
2. Create a professional, well-formatted HTML email containing the report
3. Use your send_email tool to deliver the email

Email requirements:
- Subject: Create an engaging, descriptive subject line about the research topic
- Format: Convert the markdown report into clean, professional HTML
- Style: Use appropriate HTML styling for readability
- Greeting: Include a professional greeting
- Footer: Add a professional sign-off

HTML email best practices:
- Use proper HTML structure
- Include CSS styling for better presentation
- Ensure good readability with proper spacing and typography
- Use responsive design principles
- Include a clear header with the report title
- Add section breaks for better organization

The email should look professional and be easy to read on both desktop and mobile devices.
"""

email_agent = Agent(
    name="EmailAgent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)

