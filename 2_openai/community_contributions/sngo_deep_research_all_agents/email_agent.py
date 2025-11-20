from agents import Agent, function_tool
import requests
from typing import Dict
import constants

@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send out an email with given subjecy and HTML body"""
    return requests.post(
  		"https://api.mailgun.net/v3/sandbox979b287399f848ed9122f9a12c836b17.mailgun.org/messages",
  		auth=("api", os.getenv('MAIL_GUN_API_KEY', 'MAIL_GUN_KEY')),
  		data={"from": "Mailgun Sandbox <postmaster@sandbox979b287399f848ed9122f9a12c836b17.mailgun.org>",
			"to": "Son M Ngo <sonmngo@gmail.com>",
  			"subject": subject,
  			"html": html_body})

EMAIL_INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=EMAIL_INSTRUCTIONS,
    tools=[send_email],
    model=constants.model,
)