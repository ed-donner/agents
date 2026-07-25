import os
from typing import Dict
import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool
from model_config import mimo_model


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """
    Send an email with the given subject and HTML body
    
    Args:
        subject: Email subject line
        html_body: Email body in HTML format
        
    Returns:
        Dictionary with status
    """
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        from_email = Email("example@example.com")  # Replace with your sender email
        to_email = To("example@example.com") 
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()
        response = sg.client.mail.send.post(request_body=mail)
        
        if response.status_code in [200, 201, 202]:
            return {"status": "success", "code": response.status_code}
        else:
            return {"status": "warning", "code": response.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}


INSTRUCTIONS = """You are an email communication specialist who creates professional, well-formatted emails.

**Task**: Convert a detailed research report into a beautiful HTML email.

**Email Structure:**
1. **Subject Line**: Clear, descriptive, professional (50-70 characters)
   - Should summarize the research topic
   - Example: "Research Report: AI Impact on Healthcare Delivery"

2. **Email Body (HTML)**:
   - Professional header with title
   - Executive summary in highlighted box
   - Main content with clear sections
   - Proper HTML formatting (headings, lists, emphasis)
   - Readable typography and spacing
   - Professional color scheme (blues, grays)
   - Footer with metadata (date generated, source)

**HTML Guidelines:**
- Use semantic HTML (h1, h2, h3, p, ul, ol)
- Include inline CSS for styling
- Ensure mobile-responsive design
- Use professional fonts (Arial, Helvetica, sans-serif)
- Add appropriate spacing and margins
- Highlight key findings with background colors
- Make links clickable if any URLs present

**Quality Standards:**
- Clean, modern design
- Easy to read and navigate
- Professional presentation
- Proper HTML structure
- No broken formatting

Call the send_email function exactly once with your crafted subject and HTML body."""

email_agent = Agent(
    name="EmailAgent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model=mimo_model,
)
