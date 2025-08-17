import markdown
import os
import subprocess
import tempfile
from langchain.agents import Tool

def markdown_to_pdf(filename: str) -> str:
    """Convert a markdown file to PDF format"""
    
    # Ensure filename has .md extension for input
    if not filename.endswith('.md'):
        filename += '.md'
    
    # Define paths
    sandbox_dir = "sandbox"
    md_path = os.path.join(sandbox_dir, filename)
    pdf_filename = filename.replace('.md', '.pdf')
    pdf_path = os.path.join(sandbox_dir, pdf_filename)
    
    # Check if markdown file exists
    if not os.path.exists(md_path):
        return f"Error: {filename} not found in sandbox directory"
    
    try:
        # Read markdown file
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
        
        # Add basic CSS styling with page margins
        html_with_style = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 0.75in;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 100%;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #2c3e50;
                    margin-top: 20px;
                    page-break-after: avoid;
                }}
                h1 {{
                    border-bottom: 2px solid #2c3e50;
                    padding-bottom: 10px;
                }}
                code {{
                    background-color: #f4f4f4;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                    font-size: 0.9em;
                }}
                pre {{
                    background-color: #f4f4f4;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                    border-left: 4px solid #2c3e50;
                    page-break-inside: avoid;
                }}
                pre code {{
                    padding: 0;
                    background: none;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                    page-break-inside: avoid;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                blockquote {{
                    border-left: 4px solid #2c3e50;
                    padding-left: 15px;
                    margin: 20px 0;
                    font-style: italic;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
            </style>
        </head>
        <body>
        {html_content}
        </body>
        </html>
        """
        
        # Convert HTML to PDF using WeasyPrint command-line tool
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_html:
            temp_html.write(html_with_style)
            temp_html_path = temp_html.name
        
        try:
            # Use WeasyPrint command-line tool
            result = subprocess.run([
                'weasyprint', 
                temp_html_path, 
                pdf_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return f"Error running WeasyPrint: {result.stderr}"
                
        finally:
            # Clean up temporary file
            os.unlink(temp_html_path)
        
        return f"Successfully converted {filename} to {pdf_filename} in sandbox directory"
        
    except Exception as e:
        return f"Error converting {filename} to PDF: {str(e)}"

# Create the tool
def get_markdown_pdf_tool():
    return Tool(
        name="markdown_to_pdf",
        func=markdown_to_pdf,
        description="Convert a markdown file from the sandbox directory to PDF format. Input should be the filename (with or without .md extension). Example: 'dinner.md' or 'dinner'"
    )