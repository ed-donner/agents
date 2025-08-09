import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool

print("🔧 [EMAIL AGENT] Job emailer module loaded")

@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send an email with the given subject and HTML body """
    print(f"📧 [EMAIL TOOL] Preparing to send email...")
    print(f"📧 [EMAIL TOOL] Subject: {subject}")
    print(f"📧 [EMAIL TOOL] Body length: {len(html_body)} characters")
    
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        from_email = Email("subhrajyotiroy@gmail.com") # put your verified sender here
        to_email = To("sjr8592@gmail.com") # put your recipient here
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()
        
        print("📧 [EMAIL TOOL] Sending email via SendGrid...")
        response = sg.client.mail.send.post(request_body=mail)
        print(f"📧 [EMAIL TOOL] Email response status: {response.status_code}")
        
        if response.status_code == 202:
            print("✅ [EMAIL TOOL] Email sent successfully")
        else:
            print(f"⚠️ [EMAIL TOOL] Email sent with status: {response.status_code}")
            
        return {"status": "success"}
    except Exception as e:
        print(f"❌ [EMAIL TOOL] Error sending email: {str(e)}")
        return {"status": "error", "message": str(e)}

INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a list of job postings.
You will be provided with a detailed list of job postings. You should use your tool to send one email, providing the
list converted into clean, well presented HTML with an appropriate subject line."""

print("🔧 [EMAIL AGENT] Initializing email agent...")
email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
print("✅ [EMAIL AGENT] Email agent initialized successfully")
