import os
import asyncio
from typing import Dict
from agents import Agent, OpenAIChatCompletionsModel, function_tool, Runner
from openai import AsyncOpenAI, OpenAI
import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from dotenv import load_dotenv
load_dotenv(override=True)


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send an email with the given subject and HTML body """
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        from_email = Email("sakshamsamj22@gmail.com") # put your verified sender here
        to_email = To("sk.jain2204@gmail.com") # put your recipient here
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()
        response = sg.client.mail.send.post(request_body=mail)
        print("-" * 200)
        print("Email response", response.status_code)
        print("-" * 200)
        return {"status": "success"}
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"status": "error", "message": str(e)}

INSTRUCTIONS = (
    "You are able to send a nicely formatted HTML email based on a detailed report."
    "You will be provided with a detailed report. You should use your tool to send one email, providing the" 
    "report converted into clean, well presented HTML with an appropriate subject line."
)

google_api_key = os.getenv('GOOGLE_API_KEY')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini = OpenAI(base_url=GEMINI_BASE_URL,api_key=google_api_key)

gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key,default_headers={"User-Agent": "Gemini-Client"})
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
email_agent = Agent(name="Email agent", instructions=INSTRUCTIONS, model=gemini_model, tools=[send_email])