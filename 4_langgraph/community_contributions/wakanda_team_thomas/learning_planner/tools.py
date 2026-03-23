"""
Tool definitions for the Learning Path Generator.
"""

import os
from pathlib import Path
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.tools.tavily_search import TavilySearchResults
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
    search_tool = TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=False,
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
