from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import markdown
from weasyprint import HTML
from pathlib import Path
import sys


class ConvertMarkdownContentToPdfToolInput(BaseModel):
    """File path of the file markdown to be converted to pdf"""
    markdown_content: str = Field(..., description="The markdown Content to be converted to pdf")
    output_pdf_path: str = Field(..., description="File path of the output pdf file")

class ConvertMarkdownContentToPdfTool(BaseTool):   
    name: str = "Convert Markdown Content To Pdf"
    description: str = "Convert a markdown content file to a pdf file"
    args_schema: Type[BaseModel] = ConvertMarkdownContentToPdfToolInput

    def _run(self, markdown_content: str, output_pdf_path: str) -> str:
        result = md_to_pdf(markdown_content, output_pdf_path)
        return f"✓ PDF created: {output_pdf_path} with result: {result}"

def md_to_pdf(md_content: str, pdf_file: str = None):
    """Convert markdown to PDF"""
    # Convert markdown to HTML
    print("🔄 Converting to HTML...")
    html_content = markdown.markdown(
        md_content,
        extensions=['extra', 'codehilite', 'tables', 'toc', 'fenced_code']
    )
    
    # Create styled HTML document
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 2.5cm;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-top: 20px;
            }}
            h2 {{
                color: #34495e;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
                margin-top: 15px;
            }}
            h3 {{
                color: #555;
                margin-top: 12px;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                border-left: 4px solid #3498db;
            }}
            pre code {{
                background: none;
                padding: 0;
            }}
            blockquote {{
                border-left: 4px solid #ddd;
                padding-left: 15px;
                color: #666;
                margin: 15px 0;
                font-style: italic;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #f4f4f4;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            ul, ol {{
                margin: 10px 0;
                padding-left: 30px;
            }}
            li {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert HTML to PDF
    print(f"📄 Generating PDF...")
    try:
        HTML(string=styled_html).write_pdf(pdf_file)
        print(f"✅ Success! PDF created: {pdf_file}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)