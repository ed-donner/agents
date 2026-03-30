import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import Agent, Runner, trace, function_tool, OpenAIChatCompletionsModel, input_guardrail, GuardrailFunctionOutput, enable_verbose_stdout_logging
import agents.tracing as tracing
from typing import Dict

# No domain configured for Sngrid using smtplib instead!
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load env and enable verbose logs
load_dotenv(override=True)
#enable_verbose_stdout_logging()

# Check if traces enabled.
if os.environ.get("OPENAI_API_KEY"):
    tracing.set_tracing_export_api_key(os.environ["OPENAI_API_KEY"])

# LLM Clients
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=os.getenv("DEEPSEEK_API_KEY"))
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=os.getenv("GOOGLE_API_KEY"))
llama_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=os.getenv("OPENROUTER_API_KEY"))

deepseek_model = OpenAIChatCompletionsModel(model="deepseek-chat", openai_client=deepseek_client)
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
llama3_3_model = OpenAIChatCompletionsModel(model="meta-llama/llama-3.3-8b-instruct", openai_client=llama_client)

# Sales Agent instructions
instructions1 = "You are a sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write professional, serious cold emails."

instructions2 = "You are a humorous, engaging sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write witty, engaging cold emails that are likely to get a response."

instructions3 = "You are a busy sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write concise, to the point cold emails."

sales_agent1 = Agent(name="DeepSeek Sales Agent", instructions=instructions1, model=deepseek_model)
sales_agent2 = Agent(name="Gemini Sales Agent", instructions=instructions2, model=gemini_model)
sales_agent3 = Agent(name="Llama3.3 Sales Agent", instructions=instructions3, model=llama3_3_model)

tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description="Write a cold sales email")
tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description="Write a cold sales email")
tool3 = sales_agent3.as_tool(tool_name="sales_agent3", tool_description="Write a cold sales email")


@function_tool
def send_html_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an HTML email using Gmail SMTP and your Google App Password."""
    sender_email = os.environ.get("GMAIL_USER")  # e.g. yourname@gmail.com
    sender_password = os.environ.get("GMAIL_APP_PASSWORD") # 16-character app password
    receiver_email = "andresrenaud@gmail.com"
    print("Sending email...")
    if not sender_email or not sender_password:
        return {"status": "error", "message": "GMAIL_USER or GMAIL_APP_PASSWORD not set"}

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email
    message.attach(MIMEText(html_body, "html"))


    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent.")
        return {"status": "success"}
    except Exception as e:
        print(f"Email failed: {e}")
        return {"status": "error", "message": str(e)}

# Email Sender Agent

# TOOLS: Simple email authoring tools
subject_instructions = "You can write a subject for a cold sales email. \
You are given a message and you need to write a subject for an email that is likely to get a response."

html_instructions = "You can convert a text email body to an HTML email body. \
You are given a text email body which might have some markdown \
and you need to convert it to an HTML email body with simple, clear, compelling layout and design."

# Making one call to write the subject
subject_writer = Agent(name="Email subject writer", instructions=subject_instructions, model="gpt-5-mini")
subject_tool = subject_writer.as_tool(tool_name="subject_writer", tool_description="Write a subject for a cold sales email")

# Another to convert it html
html_converter = Agent(name="HTML email body converter", instructions=html_instructions, model="gpt-5-mini")
html_tool = html_converter.as_tool(tool_name="html_converter",tool_description="Convert a text email body to an HTML email body")


instructions ="You are an email formatter and sender. You receive the body of an email to be sent. \
You first use the subject_writer tool to write a subject for the email, then use the html_converter tool to convert the body to HTML. \
Finally, you use the send_html_email tool to send the email with the subject and HTML body."


emailer_agent = Agent(
    name="Email Manager",
    instructions=instructions,
    tools=[subject_tool, html_tool, send_html_email],
    model="gpt-5-mini",
    handoff_description="Convert an email to HTML and send it",
)


# Sale Manager Agent

sales_manager_instructions = """
You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_agent tools.

Follow these steps carefully:
1. Generate Drafts: Use all three sales_agent tools to generate three different email drafts. Do not proceed until all three drafts are ready.

2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of which one is most effective.
You can use the tools multiple times if you're not satisfied with the results from the first try.

3. Handoff for Sending: Pass ONLY the winning email draft to the 'Email Manager' agent. The Email Manager will take care of formatting and sending.

Crucial Rules:
- You must use the sales agent tools to generate the drafts — do not write them yourself.
- You must hand off exactly ONE email to the Email Manager — never more than one.
"""


# Runner wrapper using the recommended trace() context manager
async def run_sales_flow():
    sales_manager = Agent(
        name="Sales Manager",
        instructions=sales_manager_instructions,
        tools=[tool1, tool2],
        handoffs=[emailer_agent],
        model="gpt-5-mini",
    )
    message = "Send out a cold sales email addressed to Dear CEO from Alice"

    with trace("Automated SDR"):
        result = await Runner.run(sales_manager, message)


if __name__ == "__main__":
    asyncio.run(run_sales_flow())