import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from agents import Agent, function_tool


@function_tool
def send_email(recipient_email: str, subject: str, html_body: str) -> Dict[str, str]:
    """
    Send an HTML email with the given subject and body to recipient_email.

    Requires in environment:
    - SENDGRID_API_KEY
    - SENDGRID_SENDER_EMAIL
    """
    api_key = os.environ.get("SENDGRID_API_KEY")
    sender = os.environ.get("SENDGRID_SENDER_EMAIL")

    if not api_key or not sender:
        msg = "Missing SENDGRID_API_KEY or SENDGRID_SENDER_EMAIL in environment."
        print(msg)
        return {"status": "error", "message": msg}

    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        from_email = Email(sender)
        to_email = To(recipient_email)
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()

        response = sg.client.mail.send.post(request_body=mail)
        print(f"SendGrid response status: {response.status_code}")
        return {"status": "success", "status_code": response.status_code}
    except Exception as e:
        msg = f"Error sending email: {e}"
        print(msg)
        return {"status": "error", "message": msg}


INSTRUCTIONS = """
You are an email composition chef.

You will receive:
- The recipient's email address.
- A completed recipe in markdown.

Your job:
1. Create a short, engaging email subject line that mentions the cuisine and dish.
2. Convert the markdown recipe into clean, readable HTML:
   - Use headings for title and sections (Ingredients, Steps, Shopping List).
   - Use bullet lists for ingredients & shopping list.
   - Use a numbered list or paragraphs for steps.
3. Call the send_email tool exactly once to send the HTML email.
4. Return a short confirmation message (do not repeat the full recipe).
"""

recipe_email_agent = Agent(
    name="RecipeEmailAgent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
