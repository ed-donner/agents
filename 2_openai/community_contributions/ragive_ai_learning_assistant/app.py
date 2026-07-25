import gradio as gr
from dotenv import load_dotenv

from learning_manager import LearningManager, UserProfile

load_dotenv(override=True)


css = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,600;1,300;1,600&family=IBM+Plex+Mono:wght@300;400&family=IBM+Plex+Sans:wght@300;400;500&display=swap');

:root {
    --bg:        #08090b;
    --card:      #111318;
    --border:    #1e2028;
    --accent:    #7eb8f7;
    --accent-lo: #3a6fa8;
    --accent-dim: rgba(126,184,247,0.08);
    --fg:        #e8eaf0;
    --fg2:       #8c90a0;
    --fg3:       #42454f;
    --r:         8px;
}

*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container {
    background: var(--bg) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    color: var(--fg) !important;
}

.gradio-container {
    max-width: 1060px !important;
    width: 96% !important;
    margin: 0 auto !important;
    padding: 48px 28px 72px !important;
}

#hdr {
    margin-bottom: 44px;
    padding-bottom: 32px;
    border-bottom: 1px solid var(--border);
}
#hdr-inner {
    display: flex;
    align-items: flex-end;
    gap: 20px;
    margin-bottom: 10px;
}
#hdr h1 {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: clamp(2.4rem, 6vw, 4rem) !important;
    font-weight: 600 !important;
    color: var(--fg) !important;
    margin: 0 !important;
    line-height: 1 !important;
    letter-spacing: -0.01em !important;
}
#hdr h1 span { color: var(--accent); font-style: italic; }
#hdr-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.2em;
    color: var(--fg3);
    text-transform: uppercase;
    padding-bottom: 6px;
}
#hdr-desc {
    font-size: 0.9rem;
    color: var(--fg3);
    font-weight: 300;
    line-height: 1.6;
    max-width: 580px;
}

#input-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 28px 32px 24px;
    margin-bottom: 20px;
}

#qbox, #qbox textarea,
.profilebox, .profilebox textarea, .profilebox input, .profilebox select {
    background: transparent !important;
    color: var(--fg) !important;
}

#qbox, #qbox textarea {
    border: none !important;
    border-bottom: 1px solid var(--border) !important;
    border-radius: 0 !important;
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.35rem !important;
    font-weight: 300 !important;
    line-height: 1.7 !important;
    padding: 10px 0 !important;
    resize: none !important;
}
#qbox:focus-within, #qbox textarea:focus {
    border-bottom-color: var(--accent) !important;
    box-shadow: none !important;
    outline: none !important;
}
#qbox label, .profilebox label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: var(--fg3) !important;
    margin-bottom: 8px !important;
}
#qbox textarea::placeholder {
    color: var(--fg3) !important;
    font-style: italic !important;
    font-family: 'Cormorant Garamond', serif !important;
}

#btn-row {
    display: flex !important;
    justify-content: flex-end !important;
    margin-top: 20px !important;
}
#run-btn {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    border-radius: var(--r) !important;
    color: var(--accent) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    padding: 9px 36px !important;
    cursor: pointer !important;
    transition: background 0.2s, color 0.2s, transform 0.1s !important;
}
#run-btn:hover {
    background: var(--accent) !important;
    color: var(--bg) !important;
    transform: translateY(-1px) !important;
}
#run-btn:active { transform: translateY(0) !important; }

#progress-container { margin-bottom: 18px !important; }

#progress-wrap {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 18px;
}
#progress-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--fg2);
    min-width: 200px;
}
#progress-bar-outer {
    flex: 1;
    height: 2px;
    background: var(--border);
    border-radius: 1px;
    overflow: hidden;
}
#progress-bar-inner {
    height: 100%;
    border-radius: 1px;
    background: var(--accent);
    transition: width 0.7s cubic-bezier(0.4, 0, 0.2, 1);
}
#progress-pct {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--accent);
    min-width: 38px;
    text-align: right;
}

#rpt {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    padding: 44px 56px !important;
    min-height: 160px !important;
    height: auto !important;
}
#rpt label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: var(--fg3) !important;
    margin-bottom: 24px !important;
    display: block !important;
}

#rpt .prose h1, #rpt .md h1 {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 2.2rem !important;
    font-weight: 600 !important;
    color: var(--fg) !important;
    border-bottom: 1px solid var(--border) !important;
    padding-bottom: 14px !important;
    margin-bottom: 24px !important;
    line-height: 1.2 !important;
}
#rpt .prose h2, #rpt .md h2 {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.5rem !important;
    font-style: italic !important;
    font-weight: 600 !important;
    color: var(--accent) !important;
    margin-top: 40px !important;
    margin-bottom: 14px !important;
    padding-left: 14px !important;
    border-left: 2px solid var(--accent) !important;
}
#rpt .prose h3, #rpt .md h3 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: var(--fg2) !important;
    margin-top: 28px !important;
    margin-bottom: 10px !important;
}
#rpt .prose p, #rpt .md p {
    font-size: 0.95rem !important;
    font-weight: 300 !important;
    line-height: 1.95 !important;
    color: var(--fg2) !important;
    margin-bottom: 12px !important;
}
#rpt .prose ul, #rpt .md ul,
#rpt .prose ol, #rpt .md ol {
    color: var(--fg2) !important;
    line-height: 1.9 !important;
    font-size: 0.95rem !important;
    font-weight: 300 !important;
    padding-left: 20px !important;
    margin-bottom: 12px !important;
}
#rpt .prose li, #rpt .md li { margin-bottom: 4px !important; }
#rpt .prose strong, #rpt .md strong {
    color: var(--fg) !important;
    font-weight: 500 !important;
}
#rpt .prose a, #rpt .md a {
    color: var(--accent) !important;
    text-decoration: underline !important;
    text-underline-offset: 3px !important;
}
#rpt .prose code, #rpt .md code {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    background: var(--accent-dim) !important;
    color: var(--accent) !important;
    padding: 2px 6px !important;
    border-radius: 3px !important;
}
#rpt .prose hr, #rpt .md hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 32px 0 !important;
}
#rpt .prose blockquote, #rpt .md blockquote {
    border-left: 2px solid var(--accent-lo) !important;
    padding-left: 16px !important;
    margin: 20px 0 !important;
    color: var(--fg3) !important;
    font-style: italic !important;
}

#rpt .generating, #rpt .progress-bar,
.generating, .progress-level, .progress-level-inner,
.progress-bar-wrap, .progress-bar-wrap .progress-bar {
    display: none !important;
    background: none !important;
    border: none !important;
    height: 0 !important;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-lo); }
"""


with gr.Blocks(theme=gr.themes.Base(), css=css) as ui:
    with gr.Column(elem_id="hdr"):
        gr.HTML("""
        <div id="hdr-inner">
            <h1>Learning <span>Path</span> Generator</h1>
        </div>
        <div id="hdr-tag">Autonomous &middot; Multi-Agent &middot; AI-Powered</div>
        <div id="hdr-desc">
            Describe your learning goal, your constraints, and where you want the result delivered.
            The system will plan skills, gather resources, write the roadmap, and export it for email,
            Notion, Google Docs, or Google Sheets workflows.
        </div>
        """)

    with gr.Column(elem_id="input-card"):
        query_textbox = gr.Textbox(
            label="Your learning goal",
            placeholder='e.g. "Become a Google Cloud Data Engineer in 3 months" or "Learn machine learning in 6 weeks"',
            lines=3,
            max_lines=8,
            elem_id="qbox",
        )

        with gr.Row():
            hours_per_week = gr.Slider(
                minimum=1,
                maximum=40,
                value=8,
                step=1,
                label="Hours per week",
                elem_classes=["profilebox"],
            )
            budget = gr.Dropdown(
                choices=["Free", "Low", "Medium", "High"],
                value="Free",
                label="Budget",
                elem_classes=["profilebox"],
            )

        with gr.Row():
            prior_experience = gr.Dropdown(
                choices=["Beginner", "Some basics", "Intermediate", "Advanced"],
                value="Beginner",
                label="Prior experience",
                elem_classes=["profilebox"],
            )
            learning_style = gr.Dropdown(
                choices=["Hands-on", "Video-first", "Reading-heavy", "Project-based", "Mixed"],
                value="Hands-on",
                label="Preferred learning style",
                elem_classes=["profilebox"],
            )

        with gr.Row():
            delivery_target = gr.Dropdown(
                choices=["Email", "Notion", "Google Docs", "Google Sheets"],
                value="Email",
                label="Delivery target",
                elem_classes=["profilebox"],
            )
            export_format = gr.Dropdown(
                choices=["DOCX", "HTML", "Markdown", "CSV"],
                value="DOCX",
                label="Export format",
                elem_classes=["profilebox"],
            )

        with gr.Row(elem_id="btn-row"):
            run_button = gr.Button("Generate Roadmap", variant="primary", elem_id="run-btn")

    progress_html = gr.HTML(value="", elem_id="progress-container", visible=False)
    report = gr.Markdown(label="Your Roadmap", elem_id="rpt")

    async def run_with_progress(
        goal: str,
        hours: int,
        budget_value: str,
        experience: str,
        style: str,
        target: str,
        export: str,
    ):
        status_map = {
            "profile captured":    (1, "Planning your skill path..."),
            "skills planned":      (2, "Researching resources..."),
            "resources gathered":  (3, "Writing your roadmap..."),
            "roadmap written":     (4, "Preparing delivery package..."),
            "delivery completed":  (5, "Done"),
            "view trace":          (0, "Initializing..."),
        }

        def make_progress_html(pct: int, label: str) -> str:
            if pct >= 100:
                return ""
            return f"""<div id="progress-wrap">
  <div id="progress-label">{label}</div>
  <div id="progress-bar-outer">
    <div id="progress-bar-inner" style="width:{pct}%"></div>
  </div>
  <div id="progress-pct">{pct}%</div>
</div>"""

        profile = UserProfile(
            available_hours_per_week=hours,
            budget=budget_value,
            prior_experience=experience,
            preferred_learning_style=style,
            delivery_target=target,
            export_format=export,
        )

        step = 0
        label = "Initializing..."
        roadmap_text = ""

        async for chunk in LearningManager().run(goal, profile):
            chunk_lower = chunk.lower().strip()

            is_status = False
            for key, (s, lbl) in status_map.items():
                if key in chunk_lower:
                    step = s
                    label = lbl
                    is_status = True
                    break

            if not is_status:
                roadmap_text += chunk

            pct = int((step / 5) * 100)
            html = make_progress_html(pct, label)
            yield gr.update(value=html, visible=(pct < 100)), gr.update(value=roadmap_text)

    run_button.click(
        fn=run_with_progress,
        inputs=[
            query_textbox,
            hours_per_week,
            budget,
            prior_experience,
            learning_style,
            delivery_target,
            export_format,
        ],
        outputs=[progress_html, report],
    )

    query_textbox.submit(
        fn=run_with_progress,
        inputs=[
            query_textbox,
            hours_per_week,
            budget,
            prior_experience,
            learning_style,
            delivery_target,
            export_format,
        ],
        outputs=[progress_html, report],
    )

ui.launch(inbrowser=True)
