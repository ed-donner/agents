import os
from agents import Agent, function_tool, Runner

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content


# Ensure this environment variable is set with your SendGrid API key
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
# Replace with your verified sender email
SENDER_EMAIL = 'mostafa.kashwaa@gmail.com'

INSTRUCTIONS = '''
You are an email agent that can send a nicely formatted HTML email based on a detailed report.
You will be given a detailed report, You should use your tools to send one email, providing the
report converted to a clean, nicely formatted HTML email with an appropriate subject line.
'''


@function_tool
def send_email(subject: str, html_content: str, recipient_email: str):
    """
    Send an email with the given subject and HTML content to the specified recipient.
    """
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    from_email = Email(SENDER_EMAIL)
    to_email = To(recipient_email)
    content = Content('text/html', html_content)
    mail = Mail(
        from_email,
        to_email,
        subject,
        content
    ).get()
    response = sg.send(mail)
    return response.status_code, response.body, response.headers


class EmailAgent:
    def __init__(self):
        self.email_agent = Agent(
            name="Email Agent",
            instructions=INSTRUCTIONS,
            tools=[send_email],
            model="gpt-4o-mini"
        )

    async def run(self, report: str, recipient_email: str):
        ''' Send an email with the report content to the specified recipient email address. '''
        print('Preparing to send email...')
        result = await Runner.run(
            self.email_agent,
            f"Report: {report}\nRecipient Email: {recipient_email}"
        )
        print('Email sent successfully!')
        return result

