import gradio as gr
import requests
from database import list_audits, get_audit, write_log
from auditor import run_audit
from util import CSS

DEF_HTML = """<html><head><title>Sample</title><meta name=\"description\" content=\"Demo article\"></head>
<body><h1>Hello world</h1><p>This is a simple demo paragraph that is fairly easy to read. It avoids complex structures.</p></body></html>"""


def fetch_url(url: str) -> str:
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        write_log("ui", "ERROR", f"fetch failed: {e}")
        return ""


def do_audit(url: str, html: str, target_keywords: str):
    if url and not html:
        html = fetch_url(url)
    if not html:
        html = DEF_HTML
    kws = [k.strip() for k in (target_keywords or "").split(",") if k.strip()]
    aid = run_audit(url or "(pasted)", html, kws)
    row = get_audit(aid)
    return aid, row.get("report_md", "")


def list_history():
    rows = list_audits(50)
    return [(r["id"], f"#{r['id']} | {r['overall_grade']} | {r['title'] or r['url']}") for r in rows]


def load_report(audit_id):
    row = get_audit(int(audit_id))
    return row.get("report_md", "")

with gr.Blocks(css=CSS, theme=gr.themes.Default(primary_hue="blue")) as demo:
    gr.Markdown("# Content Quality Auditor (MCP‑ready)\n*Fetch → Analyze → Grade → Report*")
    with gr.Row():
        url = gr.Textbox(label="URL (optional)")
        keywords = gr.Textbox(label="Target keywords (comma‑separated)")
    html = gr.Textbox(label="Paste HTML (optional)", lines=12)
    btn = gr.Button("Run Audit", variant="primary")
    aid = gr.Number(label="Audit ID", interactive=False)
    report = gr.Markdown(label="Report")

    gr.Markdown("## History")
    with gr.Row():
        hist = gr.Dropdown(choices=[], label="Past Audits", scale=3)
        refresh = gr.Button("Refresh", scale=1)
    out = gr.Markdown()

    btn.click(do_audit, [url, html, keywords], [aid, report])
    refresh.click(lambda: gr.update(choices=list_history(), value=None), None, hist)
    hist.change(load_report, hist, out)

if __name__ == "__main__":
    demo.launch()

