import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from agents.extensions.models.litellm_model import LitellmModel

from agents import (
    Agent,
    GuardrailFunctionOutput,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
    input_guardrail,
    trace,
)
from agents.exceptions import InputGuardrailTripwireTriggered, ToolInputGuardrailTripwireTriggered
from agents.tool_guardrails import ToolInputGuardrail, ToolGuardrailFunctionOutput, ToolInputGuardrailData

load_dotenv(override=True)

google_api_key = os.getenv('GEMINI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)

gemini_model = OpenAIChatCompletionsModel(model="gemini-2.5-flash", openai_client=gemini_client)
claude_model = LitellmModel(model="anthropic/claude-sonnet-4-5", api_key=anthropic_api_key)

class EmailStructuredResult(BaseModel):
    subject: str
    body: str
    unsubscribe_line:str

async def check_unsubscribe_before_send(data: ToolInputGuardrailData) -> ToolGuardrailFunctionOutput:
    import json
    args = json.loads(data.context.tool_arguments)
    html_body = args.get("html_body", "")
    if "unsubscribe" not in html_body.lower() and "opt out" not in html_body.lower():
        print("[GUARDRAIL] Unsubscribe check failed — email is missing an unsubscribe line.")
        return ToolGuardrailFunctionOutput.raise_exception(output_info={"reason": "missing unsubscribe"})
    return ToolGuardrailFunctionOutput.allow()

unsubscribe_tool_guardrail = ToolInputGuardrail(guardrail_function=check_unsubscribe_before_send)

@function_tool
def send_html_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send out an email with the given subject and HTML body to all sales prospects """
    print(f"send_html_email called. Subject: {subject}")

    gmail_address = os.environ.get('GMAIL_USER')
    app_password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = os.environ.get('EMAIL_RECIPIENT')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = gmail_address
    msg['To'] = recipient
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_address, app_password)
            server.sendmail(gmail_address, recipient, msg.as_string())
        print("Email sent successfully.")
        return {"status": "success"}
    except Exception as e:
        print(f"Email send failed: {e}")
        return {"status": "error", "error": str(e)}  

send_html_email.tool_input_guardrails = [unsubscribe_tool_guardrail]

class TopicInput(BaseModel):
    is_off_topic: bool
    topic: str
    
guardrail_topic_agent = Agent(
    name="Off Topic Check",
    instructions="Determine if the user's request is unrelated to sending or writing a sales email. "
                 "Set is_off_topic=True ONLY if the request has nothing to do with sales, cold emails, or email outreach. "
                 "Requests asking to write, send, or generate a sales or cold email should be is_off_topic=False.",
    output_type=TopicInput,
    model="gpt-4o-mini",
)

@input_guardrail
async def guardrail_against_off_topic(ctx, agent, message):
    result = await Runner.run(guardrail_topic_agent, message, context=ctx.context)
    is_off_topic = result.final_output.is_off_topic
    return GuardrailFunctionOutput(
        output_info={"off topic": result.final_output},
        tripwire_triggered=is_off_topic,
    )

instructions1 = "You are a sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write professional, serious cold emails"

instructions2 = "You are a humorous, engaging sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write witty, engaging cold emails that are likely to get a response."

instructions3 = "You are a busy sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write concise, to the point cold emails."

instructions4 = "You are an international sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write about compliance concerns from a worldwide perspective, not just the United States."

sales_agent1 = Agent(name="GPT-4o-mini Sales Agent", instructions=instructions1, model="gpt-4o-mini", output_type=EmailStructuredResult)
sales_agent2 = Agent(name="GPT-4o Sales Agent", instructions=instructions2, model="gpt-4o", output_type=EmailStructuredResult)
sales_agent3 = Agent(name="Gemini Sales Agent", instructions=instructions3, model=gemini_model, output_type=EmailStructuredResult)
sales_agent4 = Agent(name="Anthropic Sales Agent", instructions=instructions4, model=claude_model, output_type=EmailStructuredResult)

description = "Write a cold sales email"
tools = [sales_agent1.as_tool(tool_name="sales_agent1", tool_description=description),
        sales_agent2.as_tool(tool_name="sales_agent2", tool_description=description),
        sales_agent3.as_tool(tool_name="sales_agent3", tool_description=description),
        sales_agent4.as_tool(tool_name="sales_agent4", tool_description=description)]

html_instructions = "You can convert a text email body to an HTML email body. \
You are given a text email body which might have some markdown \
and you need to convert it to an HTML email body with simple, clear, compelling layout and design."

html_converter = Agent(name="HTML email body converter", instructions=html_instructions, model="gpt-4o-mini")
html_tool = html_converter.as_tool(tool_name="html_converter", tool_description="Convert a text email body to an HTML email body")

email_tools = [html_tool, send_html_email]

emailer_agent = Agent(
    name="Email Manager",
    instructions="You are an email formatter and sender. You receive the body of an email to be sent. "
                 "You MUST follow these steps in order, calling each tool exactly once: "
                 "1. Use the subject already in the message. "
                 "2. Call html_converter to convert the body to HTML. "
                 "3. Call send_html_email with the subject and HTML body. "
                 "Do not skip any step. Do not respond with text until all three tools have been called.",
    tools=email_tools,
    model="gpt-4o-mini",
    handoff_description="Convert an email to HTML and send it",
)

sales_manager_instructions = ''
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, 'system-prompt.txt')) as f:
    sales_manager_instructions = f.read().strip()

async def main():    

    print("\n--- Running Careful Sales Manager ---")
    careful_sales_manager = Agent(
        name="Sales Manager",
        instructions=sales_manager_instructions,
        tools=tools,
        handoffs=[emailer_agent],
        model="gpt-4o-mini",
        input_guardrails=[guardrail_against_off_topic]        
    )

    message = ""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, 'prompt.txt')) as f:
        message = f.read().strip()

    with trace("Protected Automated SDR"):
        try:
            result = await Runner.run(careful_sales_manager, message, max_turns=30)
        except InputGuardrailTripwireTriggered:
            print("[BLOCKED] Input guardrail triggered: message is off-topic. Stopping.")
            return
        except ToolInputGuardrailTripwireTriggered:
            print("[BLOCKED] Unsubscribe guardrail triggered: email is missing an unsubscribe line. Stopping.")
            return


if __name__ == "__main__":
    asyncio.run(main())