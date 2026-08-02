# tools.py
import os
import requests
from dotenv import load_dotenv
import sendgrid
from sendgrid.helpers.mail import (
    Email, Mail, Content, To, 
    Attachment, FileContent, FileName, FileType, Disposition
)
import base64

load_dotenv(override=True) 

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

sandbox_dir = "sandbox"
if not os.path.exists(sandbox_dir):
    os.makedirs(sandbox_dir)

def send_email(subject: str, html_body: str, file_to_attach: str = None) -> str:
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("aa@gmail.com") 
    to_email = To("aa@gmail.com")          
    
    content = Content("text/html", html_body) 
    mail = Mail(from_email, to_email, subject, content)
    
    if file_to_attach:
        file_path = os.path.join(sandbox_dir, file_to_attach)
        
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            encoded_file = base64.b64encode(data).decode()
            
            attached_file = Attachment(
                FileContent(encoded_file),
                FileName(file_to_attach),
                FileType("text/markdown"),
                Disposition("attachment")
            )
            mail.add_attachment(attached_file)
        else:
            return f"Error: File to attach '{file_to_attach}' not found in 'sandbox'."

    mail_json = mail.get()
    
    try:
        response = sg.client.mail.send.post(request_body=mail_json)
        print(f"Email response code: {response.status_code}")
        
        if 200 <= response.status_code < 300:
            status = "Email sent successfully."
            if file_to_attach:
                status += f" with attachment '{file_to_attach}'."
            return status
        else:
            return f"Error sending email: {response.body}"
    except Exception as e:
        return f"Error sending email: {e}"

def push(text: str):
    """Send a push notification to the user's device via Pushover."""
    try:
        requests.post(pushover_url, data = {
            "token": pushover_token, 
            "user": pushover_user, 
            "message": text
        })
        return "Push notification sent successfully."
    except Exception as e:
        return f"Error sending push notification: {e}"