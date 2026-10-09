from dotenv import load_dotenv
import os
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_core.tools import tool
from datetime import datetime

load_dotenv(override=True)

serper = GoogleSerperAPIWrapper()


@tool
def save_outreach_email(subject: str, html_body: str) -> str:
    """Save the final outreach email as a formatted HTML file in the sandbox directory.
    Use this after selecting the best draft to produce a ready-to-send artifact."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"sandbox/outreach_{timestamp}.html"
    full_html = (
        "<!DOCTYPE html>\n"
        "<html><head><meta charset='utf-8'>"
        f"<title>{subject}</title></head>\n"
        "<body style='font-family:Arial,sans-serif;max-width:600px;"
        "margin:0 auto;padding:20px;'>\n"
        f"<!-- Subject: {subject} | Generated: {timestamp} -->\n"
        f"{html_body}\n"
        "</body></html>"
    )
    os.makedirs("sandbox", exist_ok=True)
    with open(filename, "w") as f:
        f.write(full_html)
    return f"Email saved to {filename}"


def get_all_tools():
    search_tool = Tool(
        name="search",
        func=serper.run,
        description=(
            "Search the web for information about a company, person, role, "
            "industry trend, or recent news. Use this to research prospects "
            "before writing outreach emails."
        ),
    )

    wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    file_tools = FileManagementToolkit(root_dir="sandbox").get_tools()

    return [search_tool, wiki_tool, save_outreach_email] + file_tools
