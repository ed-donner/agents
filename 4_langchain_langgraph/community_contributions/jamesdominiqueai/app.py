import gradio as gr
import os
from analyst import DataAnalystAgent
from analyst_tools import (
    copy_uploaded_file,
    cleanup_session_sandbox,
    normalize_message_text,
    collect_charts,
)

def _init_agent():
    agent = DataAnalystAgent()
    agent.setup()
    return agent
def _show_status(text: str) -> str:
    """Return a small HTML status badge."""
    return (
        f'<div class="status-badge">'
        f'<span class="pulse"></span> {text}</div>'
    )
def _status_done(text: str) -> str:
    return f'<div class="status-badge done">{text}</div>'
def process_message(agent, message, success_criteria, dataset_file, history):
    """Run the agent and return updated UI state with HTML report + notebook."""
    if not message.strip():
        return (
            history, agent, gr.update(),
            gr.update(visible=False),
            gr.update(value="", visible=False),
            gr.update(visible=False),
            gr.update(value=None, visible=False),
            gr.update(value=""),
        )
    dataset_filename = None
    if dataset_file is not None:
        original_name = os.path.basename(dataset_file)
        copy_uploaded_file(dataset_file, original_name, agent.session_dir)
        dataset_filename = original_name
    updated_history, evaluator_feedback, _, nb_path, html_report = agent.run(
        message, success_criteria, dataset_filename, history,
    )
    evaluator_feedback = normalize_message_text(evaluator_feedback)
    
    charts = collect_charts(agent.session_dir)
    chart_update = gr.update(value=charts, visible=True) if charts else gr.update(visible=False)
    
    report_update = gr.update(value=html_report, visible=True) if html_report else gr.update(visible=False)
    
    nb_update = gr.update(value=nb_path, visible=True) if nb_path else gr.update(value=None, visible=False)
    
    chart_count = len(charts)
    status_parts = ["Analysis complete"]
    if chart_count:
        status_parts.append(f"{chart_count} chart{'s' if chart_count != 1 else ''}")
    if nb_path:
        status_parts.append("notebook ready")
    status_text = _status_done(" | ".join(status_parts))
    return (
        updated_history,
        agent,
        gr.update(value=""),
        chart_update,
        gr.update(value=evaluator_feedback, visible=bool(evaluator_feedback)),
        report_update,
        nb_update,
        gr.update(value=status_text),
    )
def reset_agent(agent):
    cleanup_session_sandbox(agent.session_dir)
    new_agent = agent.reset()
    return (
        [],
        new_agent,
        gr.update(value=""),
        gr.update(value=""),
        gr.update(value=None),
        gr.update(visible=False),
        gr.update(value="", visible=False),
        gr.update(visible=False),
        gr.update(value=None, visible=False),
        gr.update(value=""),
    )

CSS = """
/* ── Page background ─────────────────────────────────────────────────────── */
body {
    background:
        radial-gradient(ellipse at 10% 0%, rgba(99,102,241,.12), transparent 50%),
        radial-gradient(ellipse at 90% 0%, rgba(234,179,8,.10), transparent 40%),
        linear-gradient(180deg, #f8faff 0%, #eef2fb 100%);
}
.gradio-container { max-width: 1200px !important; }
/* ── Header ──────────────────────────────────────────────────────────────── */
#app-header {
    text-align: center;
    padding: 1.2rem 0 .6rem;
}
#app-header h1 {
    font-size: 1.8rem;
    background: linear-gradient(135deg, #1e40af 0%, #6366f1 55%, #d97706 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.02em;
}
#app-header p {
    color: #64748b;
    font-size: .92rem;
    margin: .3rem 0 0;
}
/* ── Cards ───────────────────────────────────────────────────────────────── */
.card {
    background: rgba(255,255,255,.92);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99,102,241,.10);
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(30,64,175,.06);
    padding: 1rem;
}
/* ── Chatbot ─────────────────────────────────────────────────────────────── */
#chatbot {
    border-radius: 16px !important;
    border: 1px solid rgba(99,102,241,.12) !important;
    box-shadow: 0 8px 32px rgba(30,64,175,.08) !important;
    background: linear-gradient(180deg, #fff 0%, #f8faff 100%) !important;
}
/* ── Input area ──────────────────────────────────────────────────────────── */
#input-group {
    background: rgba(255,255,255,.88);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(99,102,241,.10);
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(30,64,175,.05);
    padding: .8rem 1rem;
}
/* ── Buttons ─────────────────────────────────────────────────────────────── */
#go-btn {
    min-width: 140px;
    background: linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #d97706 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: .95rem !important;
    box-shadow: 0 4px 16px rgba(79,70,229,.30) !important;
    transition: transform .15s, box-shadow .15s;
}
#go-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 24px rgba(79,70,229,.36) !important;
}
#reset-btn {
    border: 1px solid rgba(239,68,68,.25) !important;
    background: rgba(254,242,242,.8) !important;
    color: #b91c1c !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    transition: background .15s;
}
#reset-btn:hover { background: rgba(254,226,226,.9) !important; }
/* ── Tabs ────────────────────────────────────────────────────────────────── */
.gr-tab-nav button {
    font-weight: 600 !important;
    color: #475569 !important;
    border-radius: 10px 10px 0 0 !important;
    transition: color .15s;
}
.gr-tab-nav button.selected {
    color: #4f46e5 !important;
    border-bottom: 2px solid #4f46e5 !important;
}
/* ── Sidebar labels ──────────────────────────────────────────────────────── */
.sidebar-label {
    font-size: .82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: #6366f1;
    margin: .6rem 0 .3rem;
}
/* ── Status badge ────────────────────────────────────────────────────────── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: .82rem;
    font-weight: 600;
    color: #4f46e5;
    padding: 4px 12px;
    border-radius: 999px;
    background: rgba(99,102,241,.08);
}
.status-badge.done { color: #15803d; background: rgba(22,163,74,.08); }
.pulse {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #4f46e5;
    animation: pulse-anim 1.4s infinite;
}
@keyframes pulse-anim {
    0%   { opacity: 1; transform: scale(1); }
    50%  { opacity: .4; transform: scale(1.4); }
    100% { opacity: 1; transform: scale(1); }
}
/* ── Gallery ─────────────────────────────────────────────────────────────── */
.gr-gallery {
    border-radius: 12px !important;
    border: 1px solid rgba(99,102,241,.08) !important;
}
/* ── File upload / download ──────────────────────────────────────────────── */
.gr-file {
    border-radius: 12px !important;
    border: 1px dashed rgba(99,102,241,.20) !important;
    background: rgba(248,250,255,.9) !important;
}
/* ── Report embed ────────────────────────────────────────────────────────── */
#tab-report > div {
    width: 100% !important;
    max-width: 100% !important;
}
#tab-report .prose {
    max-width: 100% !important;
}
/* Force dark text inside the HTML report for readability */
#tab-report .rpt,
#tab-report .rpt * {
    color: #1e293b;
}
#tab-report .rpt h1, #tab-report .rpt h2 {
    color: #3730a3;
}
#tab-report .rpt .findings {
    background: #f8faff;
    border: 1px solid #e0e7ff;
}
/* ── Tab panel backgrounds ───────────────────────────────────────────────── */
.gr-tabitem {
    background: rgba(255,255,255,.6) !important;
    border-radius: 0 0 12px 12px;
}
/* ── Misc ────────────────────────────────────────────────────────────────── */
footer { display: none !important; }
.gr-examples .gr-samples-table { border-radius: 12px !important; }
"""

with gr.Blocks(
    title="Data Analyst Agent",
    theme=gr.themes.Soft(
        primary_hue=gr.themes.colors.indigo,
        secondary_hue=gr.themes.colors.amber,
        neutral_hue=gr.themes.colors.slate,
        font=[
            gr.themes.GoogleFont("Inter"),
            "system-ui",
            "sans-serif",
        ],
    ),
    css=CSS,
) as ui:
    
    gr.HTML(
        '<div id="app-header">'
        "<h1>Data Analyst Agent</h1>"
        "<p>Upload a CSV, ask a question — the agent writes &amp; runs Python, "
        "then delivers insights you can save as a notebook.</p>"
        "</div>"
    )
    agent_state = gr.State()
    
    with gr.Row(equal_height=True):
        with gr.Column(scale=3):
            dataset_upload = gr.File(
                label="Dataset (CSV)",
                file_types=[".csv"],
                type="filepath",
                elem_classes=["card"],
            )
        with gr.Column(scale=2):
            status_html = gr.HTML(value="", elem_id="status-bar")
    
    with gr.Row(equal_height=False):
        
        with gr.Column(scale=5, min_width=440):
            chatbot = gr.Chatbot(
                label="Conversation",
                elem_id="chatbot",
                height=500,
                type="messages",
                show_copy_button=True,
                avatar_images=(
                    None,
                    "https://api.dicebear.com/9.x/bottts/svg?seed=analyst",
                ),
            )
            
            with gr.Group(elem_id="input-group"):
                message = gr.Textbox(
                    show_label=False,
                    placeholder="Ask a question about your data ...",
                    lines=1,
                    max_lines=4,
                    scale=4,
                )
                success_criteria = gr.Textbox(
                    show_label=False,
                    placeholder="Success criteria (optional) — e.g. Include correlation matrix and at least one chart",
                    lines=1,
                    max_lines=2,
                    scale=4,
                )
                with gr.Row():
                    reset_btn = gr.Button(
                        "Reset",
                        variant="stop",
                        elem_id="reset-btn",
                        size="sm",
                    )
                    go_btn = gr.Button(
                        "Analyse",
                        variant="primary",
                        elem_id="go-btn",
                        size="lg",
                    )
        
        with gr.Column(scale=4, min_width=360):
            with gr.Tabs():
                # Tab 1 — Report
                with gr.Tab("Report", id="tab-report"):
                    report_html = gr.HTML(
                        label="Analysis Report",
                        visible=False,
                    )
                    gr.Markdown(
                        "<p style='text-align:center;color:#94a3b8;font-size:.85rem'>"
                        "Run an analysis to see the report here.</p>",
                        elem_id="report-placeholder",
                    )
                # Tab 2 — Charts
                with gr.Tab("Charts", id="tab-charts"):
                    chart_gallery = gr.Gallery(
                        label="Generated Charts",
                        columns=2,
                        rows=2,
                        visible=False,
                        height=400,
                        object_fit="contain",
                    )
                    gr.Markdown(
                        "<p style='text-align:center;color:#94a3b8;font-size:.85rem'>"
                        "Charts will appear here after analysis.</p>",
                        elem_id="charts-placeholder",
                    )
                # Tab 3 — Save / Download
                with gr.Tab("Save", id="tab-save"):
                    gr.HTML(
                        '<p class="sidebar-label">Download Notebook</p>'
                        '<p style="color:#64748b;font-size:.85rem">'
                        "The notebook (.ipynb) bundles your analysis code, "
                        "charts, and findings in one file.</p>"
                    )
                    notebook_download = gr.File(
                        label="Notebook (.ipynb)",
                        visible=False,
                        interactive=False,
                    )
                # Tab 4 — Evaluator
                with gr.Tab("Evaluator", id="tab-eval"):
                    gr.Markdown(
                        "<p style='color:#64748b;font-size:.85rem'>"
                        "Internal quality evaluator feedback.</p>"
                    )
                    evaluator_feedback = gr.Markdown(visible=False)
    
    gr.Examples(
        examples=[
            [
                "What are the key trends in this dataset? Detect any outliers.",
                "Include at least one chart",
            ],
            [
                "Run a correlation analysis and identify the top 3 most correlated pairs.",
                "",
            ],
            [
                "Forecast the next 3 periods using a simple linear trend.",
                "",
            ],
        ],
        inputs=[message, success_criteria],
        label="Quick-start prompts",
    )
    
    ui.load(_init_agent, [], [agent_state])
    shared_inputs = [agent_state, message, success_criteria, dataset_upload, chatbot]
    shared_outputs = [
        chatbot, agent_state, message, chart_gallery, evaluator_feedback,
        report_html, notebook_download, status_html,
    ]
    go_btn.click(process_message, shared_inputs, shared_outputs)
    message.submit(process_message, shared_inputs, shared_outputs)
    reset_btn.click(
        reset_agent,
        [agent_state],
        [
            chatbot, agent_state, message, success_criteria, dataset_upload,
            chart_gallery, evaluator_feedback, report_html, notebook_download,
            status_html,
        ],
    )
if __name__ == "__main__":
    ui.launch(inbrowser=True)
