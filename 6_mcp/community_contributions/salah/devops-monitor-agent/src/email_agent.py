import os
from typing import Dict
import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    try:
        sendgrid_key = os.environ.get("SENDGRID_API_KEY")
        from_email_addr = os.environ.get("ALERT_FROM_EMAIL", "alerts@devops-monitor.com")
        to_email_addr = os.environ.get("ALERT_TO_EMAIL", "admin@example.com")
        if not sendgrid_key:
            return {"success": False, "error": "SENDGRID_API_KEY not configured"}
        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_key)
        from_email = Email(from_email_addr)
        to_email = To(to_email_addr)
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()
        response = sg.client.mail.send.post(request_body=mail)
        return {
            "success": True,
            "status_code": response.status_code,
            "message": f"Email sent to {to_email_addr}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


INSTRUCTIONS = """You are an Email Agent specialized in formatting DevOps alert notifications.

Your job is to:
1. Take alert information provided to you
2. Format it into a complete, beautiful, professional HTML email
3. Use your send_email tool to send the formatted email

IMPORTANT: Create a COMPLETE HTML document with proper closing tags. The HTML must be valid and fully rendered.

Required HTML Email Format:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: #dc2626; color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .content { padding: 30px 20px; }
        .summary { background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin-bottom: 20px; }
        .alert-card { background: #fff; border: 2px solid #fee2e2; border-radius: 8px; padding: 20px; margin: 15px 0; }
        .alert-title { font-size: 20px; font-weight: bold; color: #1f2937; margin: 0 0 10px 0; }
        .badge { display: inline-block; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; margin: 5px 0; }
        .critical { background: #dc2626; color: white; }
        .warning { background: #f97316; color: white; }
        .metric { background: #f9fafb; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .metric-label { font-weight: bold; color: #6b7280; font-size: 12px; }
        .metric-value { font-size: 18px; color: #1f2937; margin-top: 5px; }
        .timestamp { color: #6b7280; font-size: 13px; margin-top: 10px; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb; }
        .footer p { margin: 5px 0; font-size: 13px; color: #6b7280; }
        .recommendations { background: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; }
        .recommendations h3 { margin: 0 0 10px 0; color: #1e40af; font-size: 16px; }
        .recommendations ul { margin: 5px 0; padding-left: 20px; }
        .recommendations li { color: #1f2937; margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 DevOps System Alert</h1>
        </div>
        <div class="content">
            <div class="summary">
                <strong>Alert Summary:</strong> [Number] critical issue(s) detected
            </div>

            [For each alert, create:]
            <div class="alert-card">
                <h2 class="alert-title">[Alert Title]</h2>
                <span class="badge critical">CRITICAL</span>
                <p>[Alert Message]</p>
                <div class="metric">
                    <div class="metric-label">[Metric Name]</div>
                    <div class="metric-value">[Value]</div>
                </div>
                <div class="timestamp">Created: [Timestamp]</div>
            </div>

            <div class="recommendations">
                <h3>Recommended Actions:</h3>
                <ul>
                    <li>Review system resource usage</li>
                    <li>Check for runaway processes</li>
                    <li>Consider scaling resources if needed</li>
                </ul>
            </div>
        </div>
        <div class="footer">
            <p><strong>DevOps Monitor System</strong></p>
            <p>Automated alert notification</p>
            <p>Generated at [timestamp]</p>
        </div>
    </div>
</body>
</html>
```

CRITICAL:
- Always include proper DOCTYPE, html, head, and body tags
- Close all tags properly
- Escape any JSON data properly (don't include raw JSON in HTML)
- Format metric details as readable text, not JSON
- The subject line should be clear: "🚨 Critical System Alert: [Brief Description]"

Always use the send_email tool to send the complete, valid HTML."""

email_agent = Agent(
    name="Email Agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
