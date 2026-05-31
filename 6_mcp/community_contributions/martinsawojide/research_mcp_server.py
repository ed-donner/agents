"""Single MCP server: Tavily search + SendGrid email (stdio). Launched via uv run from this folder."""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail, To
from tavily import AsyncTavilyClient

load_dotenv(override=True)

mcp = FastMCP("deep_research_server")


@mcp.tool()
async def tavily_search(query: str) -> str:
    """Search the web for the given query and return a summary with sources.

    Args:
        query: The search query string.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not set."
    client = AsyncTavilyClient(api_key=api_key)
    response = await client.search(
        query,
        max_results=5,
        search_depth="basic",
        include_answer=True,
    )

    sections = []
    if response.get("answer"):
        sections.append(f"## Summary\n{response['answer']}")
    if response.get("results"):
        sections.append("## Sources")
        for r in response["results"]:
            sections.append(f"**{r['title']}**\nSource: {r['url']}\n{r['content']}")
    return "\n\n".join(sections) if sections else "No results."


@mcp.tool()
def send_email(subject: str, html_body: str) -> str:
    """Send an email with the given subject and HTML body using SendGrid.

    Args:
        subject: Email subject line.
        html_body: HTML content for the email body.
    """
    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        return "Error: SENDGRID_API_KEY is not set."

    from_email_addr = os.getenv("SENDGRID_FROM_EMAIL", "awojidemartins@gmail.com")
    to_email_addr = os.getenv("SENDGRID_TO_EMAIL", "awojidemartins@gmail.com")

    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    from_email = Email(from_email_addr)
    to_email = To(to_email_addr)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    return f"success (status {response.status_code})"


if __name__ == "__main__":
    mcp.run(transport="stdio")
