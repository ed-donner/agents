import gradio as gr
import requests
from auditor import run_audit_agent


DEF_HTML = """<html><head><title>Sample</title><meta name="description" content="Demo article"></head>
<body><h1>Hello world</h1><p>This is a simple demo paragraph that is fairly easy to read. It avoids complex structures.</p></body></html>"""

def fetch_url(url: str) -> str:
    if not url:
        return ""
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return f"Error fetching URL: {e}"

async def do_audit(url: str, html: str, target_keywords: str):
    """Main handler for the UI button."""
    if url and not html:
        html = fetch_url(url)
    if not html.strip():
        html = DEF_HTML

    query = (
        f"Run a full audit on this content.\n\n"
        f"URL: {url or 'N/A'}\n"
        f"Target Keywords: {target_keywords or 'None'}\n"
        f"HTML:\n{html[:5000]}" 
    )

    try:
        response = await run_audit_agent(query)
    except Exception as ex:
        response = f"Agent error: {ex}"

    return response


with gr.Blocks(theme=gr.themes.Default(primary_hue="blue")) as demo:
    gr.Markdown("## Content Quality Auditor (MCP-Ready)\n**Fetch → Analyze → Grade → Report**")

    with gr.Row():
        url = gr.Textbox(label="URL (optional)", placeholder="https://example.com/article")
        keywords = gr.Textbox(label="Target Keywords (comma-separated)", placeholder="e.g., AI, automation, content")

    html = gr.Textbox(label="Paste HTML (optional)", lines=12, placeholder="Paste your article HTML here...")
    run_btn = gr.Button("Run Audit", variant="primary")
    report = gr.Markdown(label="Audit Report")

    run_btn.click(do_audit, [url, html, keywords], [report])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7864, share=False)
