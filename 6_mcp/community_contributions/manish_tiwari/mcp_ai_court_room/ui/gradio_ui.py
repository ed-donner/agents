"""Gradio courtroom: case on top; Lawyer 1 | Judge | Lawyer 2 with streaming text."""

from __future__ import annotations

import os
import socket

import gradio as gr
from rich.console import Console

from core.debate_engine import DebateEngine

console = Console()

CUSTOM_CSS = """
.gradio-container { max-width: 1600px !important; margin: auto; }
.court-header {
  text-align: center;
  padding: 1.1rem 1.25rem;
  background: linear-gradient(135deg, #0a1628 0%, #0d1b3d 45%, #152c52 100%);
  color: #e8eef7;
  border-radius: 12px;
  margin-bottom: 1rem;
  border: 1px solid #1e3a5f;
  box-shadow: 0 4px 14px rgba(10, 22, 40, 0.35);
}
.court-header h1 { color: #f0f4ff !important; text-shadow: 0 1px 2px rgba(0,0,0,0.25); }
.court-header p { color: #b8c9e0 !important; }
.panel-title {
  font-weight: 700;
  color: #c9a227;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-size: 0.85rem;
  margin-bottom: 0.35rem;
}
.case-panel {
  border-left: 4px solid #c9a227;
  padding: 12px 16px;
  background: #faf8f3;
  border-radius: 8px;
  margin-bottom: 1rem;
}
.bench-column {
  border-left: 3px solid #8b2942;
  border-right: 3px solid #8b2942;
  padding: 0 10px;
  background: linear-gradient(180deg, #f8f5f7 0%, #ffffff 100%);
  border-radius: 8px;
}
.counsel-left {
  border-left: 3px solid #1e5f74;
  padding-left: 10px;
  background: #f4fafc;
  border-radius: 8px;
}
.counsel-right {
  border-left: 3px solid #6b4c9a;
  padding-left: 10px;
  background: #f7f4fc;
  border-radius: 8px;
}
.stream-box textarea {
  font-family: 'Source Serif 4', 'Georgia', serif !important;
  line-height: 1.45 !important;
  font-size: 15px !important;
}
"""


def build_demo():
    # theme/css on Blocks: some Gradio versions reject them on launch()
    with gr.Blocks(
        title="AI Courtroom Debate Simulator",
        theme=gr.themes.Soft(primary_hue="amber", neutral_hue="slate"),
        css=CUSTOM_CSS,
    ) as demo:
        gr.HTML(
            """
            <div class="court-header">
              <h1 style="margin:0; font-size:1.65rem;">⚖️ AI Courtroom Debate Simulator</h1>
              <p style="margin:0.55rem 0 0 0; font-size:0.95rem;">
                Live MCP research · left: plaintiff counsel · center: bench and verdict · right: defense
              </p>
            </div>
            """
        )

        status = gr.Textbox(label="Session status", interactive=False, max_lines=2)

        with gr.Column(elem_classes=["case-panel"]):
            gr.Markdown(
                '<p class="panel-title">Case source</p>'
                "<p style='margin:0 0 8px 0; font-size:0.9rem; opacity:0.85;'>"
                "Optional: paste your own matter (title, parties, facts). "
                "Leave empty to <strong>search the open web</strong> for a recent case—"
                "the query includes <strong>today’s date</strong> for recency.</p>"
            )
            user_case_notes = gr.Textbox(
                label="Your case details (optional)",
                lines=6,
                max_lines=12,
                placeholder=(
                    "Example: Case: Smith v. Jones. Plaintiff seeks… Defendant argues… "
                    "Leave blank to auto-fetch a latest public legal matter."
                ),
                show_label=True,
            )

        with gr.Column(elem_classes=["case-panel"]):
            gr.Markdown('<p class="panel-title">Case (resolved)</p>')
            case_panel = gr.Markdown("_Start the session to load or resolve the matter._")

        with gr.Row(equal_height=True):
            with gr.Column(scale=1, elem_classes=["counsel-left"]):
                gr.Markdown('<p class="panel-title">Lawyer 1 — plaintiff / claimant</p>')
                lawyer1_box = gr.Textbox(
                    label="Argument",
                    lines=22,
                    max_lines=40,
                    show_label=False,
                    placeholder="Opening arguments will stream here…",
                    elem_classes=["stream-box"],
                )

            with gr.Column(scale=1, elem_classes=["bench-column"]):
                gr.Markdown('<p class="panel-title">Judge — observations & final result</p>')
                judge_box = gr.Textbox(
                    label="Bench",
                    lines=22,
                    max_lines=40,
                    show_label=False,
                    placeholder="Round-by-round bench notes, then FINAL VERDICT streams here…",
                    elem_classes=["stream-box"],
                )

            with gr.Column(scale=1, elem_classes=["counsel-right"]):
                gr.Markdown('<p class="panel-title">Lawyer 2 — defense</p>')
                lawyer2_box = gr.Textbox(
                    label="Argument",
                    lines=22,
                    max_lines=40,
                    show_label=False,
                    placeholder="Rebuttals stream here…",
                    elem_classes=["stream-box"],
                )

        with gr.Row():
            start = gr.Button("▶ Begin trial (streaming)", variant="primary", scale=2)
            gr.Markdown(
                "_Rounds 1–3: each side streams in its column; the judge column streams bench notes, then the **FINAL VERDICT**._"
            )

        async def run_streaming_trial(case_notes: str):
            engine = DebateEngine()
            raw = (case_notes or "").strip()
            optional = raw if raw else None
            async for snap in engine.run_streaming(optional_case_details=optional):
                yield (
                    snap.case_md,
                    snap.lawyer1_text,
                    snap.judge_text,
                    snap.lawyer2_text,
                    snap.status,
                )

        start.click(
            fn=run_streaming_trial,
            inputs=[user_case_notes],
            outputs=[
                case_panel,
                lawyer1_box,
                judge_box,
                lawyer2_box,
                status,
            ],
        )

    return demo


def _first_free_port(host: str, preferred: int, max_tries: int = 50) -> int:
    """Use `preferred` if free; otherwise try the next ports (e.g. 7860 → 7861 …)."""
    if host == "0.0.0.0":
        bind_host = "0.0.0.0"
    elif host in ("127.0.0.1", "localhost", ""):
        bind_host = "127.0.0.1"
    else:
        bind_host = host
    for offset in range(max_tries):
        port = preferred + offset
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((bind_host, port))
        except OSError:
            continue
        return port
    raise OSError(
        f"No free TCP port between {preferred} and {preferred + max_tries - 1}. "
        "Set GRADIO_SERVER_PORT or free a port (another Gradio app may be on 7860)."
    )


def launch_ui() -> None:
    # Hugging Face Spaces set SPACE_ID; Gradio must bind 0.0.0.0:7860 for the proxy.
    on_hf_space = bool(os.getenv("SPACE_ID"))
    if on_hf_space:
        host = "0.0.0.0"
        port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
        share = False
        open_browser = False
    else:
        host = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
        preferred = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
        share = os.getenv("GRADIO_SHARE", "").lower() in ("1", "true", "yes")
        port = _first_free_port(host, preferred)
        if port != preferred:
            console.print(
                f"[yellow]Port {preferred} is in use; using {port} instead.[/yellow]"
            )
        open_browser = os.getenv("GRADIO_NO_INBROWSER", "").lower() not in (
            "1",
            "true",
            "yes",
        )

    demo = build_demo()
    demo.queue(default_concurrency_limit=1)
    console.print(
        f"[green]Opening Gradio on http://{host}:{port}[/green] — click “Begin trial”."
    )
    demo.launch(
        server_name=host,
        server_port=port,
        share=share,
        show_error=True,
        inbrowser=open_browser,
    )
