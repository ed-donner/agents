"""
Tool definitions for the Learning Path Generator.
"""

import os
from pathlib import Path
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_tavily import TavilySearch
from langchain.agents import Tool
from dotenv import load_dotenv

load_dotenv(override=True)

SANDBOX_DIR = Path(__file__).parent / "sandbox"


def get_wikipedia_tool():
    """Create and return the Wikipedia search tool."""
    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
    return wiki_tool


def get_search_tool():
    """Create and return the Tavily web search tool."""
    search_tool = TavilySearch(
        max_results=5,
        topic="general",
    )
    return search_tool


def write_markdown_file(filename: str, content: str) -> str:
    """Write content to a markdown file in the sandbox directory."""
    SANDBOX_DIR.mkdir(exist_ok=True)
    
    if not filename.endswith(".md"):
        filename = f"{filename}.md"
    
    filepath = SANDBOX_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    
    return f"Successfully wrote {len(content)} characters to {filepath}"


def get_file_write_tool():
    """Create and return the file write tool."""
    file_tool = Tool(
        name="write_markdown",
        func=lambda x: write_markdown_file(x.split("|||")[0].strip(), x.split("|||")[1]),
        description="Write content to a markdown file. Input format: 'filename|||content'"
    )
    return file_tool


def generate_pdf_from_markdown(markdown_content: str, filename: str) -> str:
    """Convert markdown content to a styled PDF file."""
    import markdown2
    from weasyprint import HTML, CSS
    
    SANDBOX_DIR.mkdir(exist_ok=True)
    
    if not filename.endswith(".pdf"):
        filename = f"{filename}.pdf"
    
    html_content = markdown2.markdown(
        markdown_content,
        extras=["tables", "fenced-code-blocks", "header-ids"]
    )
    
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Learning Path</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    css = CSS(string="""
        body {{
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            margin: 40px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        a {{
            color: #3498db;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        ul, ol {{
            margin-left: 20px;
        }}
        li {{
            margin-bottom: 5px;
        }}
    """)
    
    filepath = SANDBOX_DIR / filename
    HTML(string=styled_html).write_pdf(filepath, stylesheets=[css])
    
    return f"Successfully generated PDF: {filepath}"


def send_email_with_pdf(
    to_email: str,
    subject: str,
    body_html: str,
    pdf_path: str,
) -> str:
    """Send an email with a PDF attachment using Resend API."""
    import base64
    import requests
    
    resend_api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL", "Learning Planner <onboarding@resend.dev>")
    
    if not resend_api_key:
        return "Error: RESEND_API_KEY not found in environment variables"
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        return f"Error: PDF file not found at {pdf_path}"
    
    pdf_content = base64.b64encode(pdf_file.read_bytes()).decode("utf-8")
    
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": body_html,
        "attachments": [
            {
                "filename": pdf_file.name,
                "content": pdf_content,
            }
        ]
    }
    
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 200:
        return f"Successfully sent email to {to_email} with {pdf_file.name} attached"
    else:
        return f"Error sending email: {response.status_code} - {response.text}"


def create_email_body(topic: str, total_phases: int, total_days: int) -> str:
    """Create a styled HTML email body for the learning path notification."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                Your Learning Path is Ready!
            </h1>
            
            <p>Hi,</p>
            
            <p>Your personalized learning path for <strong>{topic}</strong> has been generated.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: #34495e; margin-top: 0;">Key Highlights:</h3>
                <ul>
                    <li><strong>{total_phases}</strong> phases covering prerequisites to advanced topics</li>
                    <li>Estimated completion: <strong>{total_days} days</strong></li>
                    <li>Includes hands-on projects for each phase</li>
                </ul>
            </div>
            
            <p>The full learning path is attached as a PDF document.</p>
            
            <p style="color: #7f8c8d; font-size: 14px; margin-top: 30px;">
                Happy learning!<br>
                <em>Learning Path Generator</em>
            </p>
        </div>
    </body>
    </html>
    """
