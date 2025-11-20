import markdown
from datetime import datetime
import os

REPORTS_DIR = "reports"
REPORTS_DIR = os.path.join(os.path.dirname(__file__), REPORTS_DIR)
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_html_report(markdown_content: str, query: str, filename: str = None) -> tuple[str, str]:
    """
    Convert markdown clinical report to HTML and save it.
    
    Args:
        markdown_content: The markdown report content
        query: Original clinical query
        filename: Optional filename (auto-generated if not provided)
    
    Returns:
        Tuple of (html_content, filepath)
    """
    # Convert markdown to HTML
    html_body = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code', 'nl2br']
    )
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create complete HTML document
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pharmacogenomic Clinical Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            border-radius: 10px;
        }}
        
        .header {{
            border-bottom: 4px solid #3498db;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .meta-info {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }}
        
        .meta-info p {{
            margin: 5px 0;
            font-size: 14px;
            color: #555;
        }}
        
        .meta-info strong {{
            color: #2c3e50;
        }}
        
        .content h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 22px;
        }}
        
        .content h3 {{
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 18px;
        }}
        
        .content p {{
            margin-bottom: 15px;
            text-align: justify;
        }}
        
        .content ul, .content ol {{
            margin-left: 30px;
            margin-bottom: 15px;
        }}
        
        .content li {{
            margin-bottom: 8px;
        }}
        
        .content a {{
            color: #3498db;
            text-decoration: none;
            border-bottom: 1px dotted #3498db;
        }}
        
        .content a:hover {{
            color: #2980b9;
            border-bottom: 1px solid #2980b9;
        }}
        
        .content blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            color: #555;
            background: #f8f9fa;
            padding: 15px 20px;
        }}
        
        .content code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }}
        
        .content pre {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        
        .content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        .content table th {{
            background: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        
        .content table td {{
            padding: 10px;
            border: 1px solid #ddd;
        }}
        
        .content table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            background: #3498db;
            color: white;
            margin-right: 5px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 24px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 Pharmacogenomic Clinical Report</h1>
        </div>
        
        <div class="meta-info">
            <p><strong>Query:</strong> {query}</p>
            <p><strong>Generated:</strong> {timestamp}</p>
            <p><strong>Report Type:</strong> <span class="badge">Oncology</span> <span class="badge">Pharmacogenomics</span></p>
        </div>
        
        <div class="content">
            {html_body}
        </div>
        
        <div class="footer">
            <p>This report is generated for research and educational purposes only.</p>
            <p>Clinical decisions should be made in consultation with qualified healthcare professionals.</p>
            <p>Generated by Pharmacogenomic Clinical Report Generator</p>
        </div>
    </div>
</body>
</html>"""
    
    # Generate filename if not provided
    if not filename:
        timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp_file}.html"
    
    # Ensure reports directory exists
    reports_dir = REPORTS_DIR
    
    # Save file
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return html_content, filepath

