import os, requests
from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool

from fastmcp import FastMCP

load_dotenv(override=True)

mcp = FastMCP("Sales Agent Tools Server")

@mcp.tool()
async def serious_agent(prompt: str) -> str:
    "use this for generating serious emails. show the user the email when ready."

    instructions = "You are a sales agent working for ComplAI, \
    a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
    You write professional, serious cold emails."

    sales_agent = Agent(
        name="Professional Sales Agent",
        instructions=instructions,
        model="gpt-4o-mini",
    )

    with trace("serious agent"):
        results = await Runner.run(sales_agent, prompt)

    return results.final_output


@mcp.tool()
async def humorous_agent(prompt: str) -> str:
    "use this for generating humorous emails. show the user the email when ready."

    instructions = "You are a humorous, engaging sales agent working for ComplAI, \
        a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
        You write witty, engaging cold emails that are likely to get a response."

    sales_agent = Agent(
        name="Humorous Sales Agent",
        instructions=instructions,
        model="gpt-4o-mini",
    )

    with trace("humorous agent"):
        results = await Runner.run(sales_agent, prompt)

    return results.final_output


@mcp.tool()
async def busy_agent(prompt: str) -> str:
    "use this for generating busy emails. show the user the email when ready."

    instructions = "You are a busy sales agent working for ComplAI, \
    a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
    You write concise, to the point cold emails."

    sales_agent = Agent(
        name="Busy Sales Agent",
        instructions=instructions,
        model="gpt-4o-mini",
    )

    with trace("busy agent"):
        results = await Runner.run(sales_agent, prompt)

    return results.final_output


@mcp.tool()
async def converter_agent(body: str) -> str:
    "use this for formatting the body of emails to an HTML body before sending the email"

    instructions = "You can convert a text email body to an HTML email body. \
    You are given a text email body which might have some markdown \
    and you need to convert it to an HTML email body with simple, clear, compelling layout and design."

    converter_agent = Agent(
        name="HTML email body converter",
        instructions=instructions,
        model="gpt-4o-mini",
    )

    with trace("converter agent"):
        results = await Runner.run(converter_agent, body)

    return results.final_output


@mcp.tool()
def send_email(subject: str, body: str):
    """Send out an email with the given HTML body. Make sure the user approves the email before sending."""
    
    # Set up email sender, recipient, and content
    from_email = "onboarding@resend.dev"  # Replace with your verified sender
    to_email = "CHANGEME@CHANGEME.com"  # Replace with recipient's email
    
    # Resend API headers and payload
    headers = {
        "Authorization": f"Bearer {os.getenv("RESEND_API_KEY")}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": from_email,
        "to": to_email,
        "subject": subject,
        "html": f"<p>{body}</p>"
    }
    
    # Send email using Resend API
    response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 202 or response.status_code == 200:
        return {"status": "success"}
    else:
        return {"status": "failure", "message": response.text}


if __name__ == "__main__":
    try:
        mcp.run(transport="http", host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        exit(0)  
