"""Gradio UI: Nothing OS inspired design."""

import warnings
warnings.filterwarnings("ignore", message=".*Resolved model mismatch.*")
warnings.filterwarnings("ignore", message=".*PydanticSerializationUnexpectedValue.*")

import asyncio
import queue
import logging
import re
import sys
import threading
from pathlib import Path

import gradio as gr
from main import run_pipeline, SANDBOX


log_queue: queue.Queue[str] = queue.Queue()
stage_queue: queue.Queue[str] = queue.Queue()

class _UIHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        from datetime import datetime
        msg = record.getMessage()
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        if msg.startswith("[STAGE]"):
            stage_queue.put_nowait(msg[len("[STAGE]"):].strip())
        else:
            log_queue.put_nowait(f"[{ts}] {msg}")

_handler = _UIHandler()
for _name in ["autogen_core.trace", "scout", "committee", "aggregator", "tools", "stage"]:
    _l = logging.getLogger(_name)
    _l.addHandler(_handler)
    _l.setLevel(logging.DEBUG)


_done = threading.Event()
_result: dict[str, Path] = {}
_error = ""


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[=>]|\r")


class _StdoutTee:
    """Write to both the real stdout and the UI log queue, line by line."""
    def __init__(self, real):
        self._real = real
        self._buf = ""

    def write(self, text: str) -> int:
        self._real.write(text)
        clean = _ANSI_RE.sub("", text)
        self._buf += clean
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip():
                log_queue.put_nowait(line.strip())
        return len(text)

    def flush(self):
        self._real.flush()

    def __getattr__(self, name):
        return getattr(self._real, name)


def _run(url: str, cv_paths: list[str], template: str) -> None:
    global _result, _error
    real_stdout = sys.stdout
    sys.stdout = _StdoutTee(real_stdout)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _result = loop.run_until_complete(run_pipeline(url, cv_paths, template))
        _error = ""
    except Exception as e:
        _error = str(e)
        _result = {}
    finally:
        sys.stdout = real_stdout
        _done.set()


def start(url: str, cv_files: list | None, tpl_file: str | None, tpl_text: str):
    global _result, _error
    if not url or not url.strip():
        return "⚠ Enter a job URL.", "Ready", gr.update()
    if not cv_files:
        return "⚠ Upload at least one CV file.", "Ready", gr.update()

    _done.clear()
    _result, _error = {}, ""

    for q in (log_queue, stage_queue):
        while not q.empty():
            try:
                q.get_nowait()
            except queue.Empty:
                break

    paths = [f if isinstance(f, str) else getattr(f, "name", str(f)) for f in cv_files]
    template = ""
    if tpl_file:
        p = tpl_file if isinstance(tpl_file, str) else getattr(tpl_file, "name", str(tpl_file))
        template = Path(p).read_text(encoding="utf-8")
    elif tpl_text and tpl_text.strip():
        template = tpl_text.strip()

    threading.Thread(target=_run, args=(url.strip(), paths, template), daemon=True).start()
    return "", "Scraping job page...", gr.update(interactive=False, value="Running…")


def poll_stage(current: str):
    latest = current
    while not stage_queue.empty():
        try:
            latest = stage_queue.get_nowait()
        except queue.Empty:
            break
    if _done.is_set():
        label = f"Done — {_error}" if _error else "Done — outputs ready for download."
        return label, gr.update(interactive=True, value="Run Agent")
    return latest, gr.update()


def poll_logs(current: str) -> str:
    lines = []
    while not log_queue.empty():
        try:
            lines.append(log_queue.get_nowait())
        except queue.Empty:
            break
    return current + "\n".join(lines) + ("\n" if lines else "")


def poll_downloads():
    if not _done.is_set():
        return (gr.update(interactive=False),) * 4

    typst  = SANDBOX / "tailored_resume.typ"
    qa     = SANDBOX / "application_answers.txt"
    report = SANDBOX / "alignment_report.md"
    pdf    = SANDBOX / "tailored_resume.pdf"

    return (
        gr.update(value=str(typst),  interactive=True) if typst.exists()  else gr.update(interactive=False),
        gr.update(value=str(qa),     interactive=True) if qa.exists()     else gr.update(interactive=False),
        gr.update(value=str(report), interactive=True) if report.exists() else gr.update(interactive=False),
        gr.update(value=str(pdf),    interactive=True) if pdf.exists()    else gr.update(interactive=False),
    )


theme = gr.themes.Base(
    primary_hue="neutral",
    secondary_hue="neutral",
    neutral_hue="neutral",
    radius_size="none",
    text_size="md",
    spacing_size="md",
    font=[gr.themes.GoogleFont("Space Grotesk"), "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("Space Mono"), "ui-monospace", "monospace"],
).set(
    body_background_fill="#0a0a0a",
    body_background_fill_dark="#0a0a0a",
    background_fill_primary="#111111",
    background_fill_primary_dark="#111111",
    background_fill_secondary="#1a1a1a",
    background_fill_secondary_dark="#1a1a1a",
    block_background_fill="#111111",
    block_background_fill_dark="#111111",
    block_border_color="#2a2a2a",
    block_border_color_dark="#2a2a2a",
    block_label_background_fill="#1a1a1a",
    block_label_background_fill_dark="#1a1a1a",
    block_label_text_color="#888888",
    block_label_text_color_dark="#888888",
    block_title_text_color="#ffffff",
    block_title_text_color_dark="#ffffff",
    body_text_color="#e8e8e8",
    body_text_color_dark="#e8e8e8",
    input_background_fill="#1a1a1a",
    input_background_fill_dark="#1a1a1a",
    input_border_color="#2a2a2a",
    input_border_color_dark="#2a2a2a",
    input_placeholder_color="#555555",
    input_placeholder_color_dark="#555555",
    button_primary_background_fill="#ff3c00",
    button_primary_background_fill_dark="#ff3c00",
    button_primary_background_fill_hover="#cc3000",
    button_primary_background_fill_hover_dark="#cc3000",
    button_primary_text_color="#ffffff",
    button_primary_text_color_dark="#ffffff",
    button_secondary_background_fill="#1a1a1a",
    button_secondary_background_fill_dark="#1a1a1a",
    button_secondary_background_fill_hover="#2a2a2a",
    button_secondary_background_fill_hover_dark="#2a2a2a",
    button_secondary_text_color="#e8e8e8",
    button_secondary_text_color_dark="#e8e8e8",
    button_secondary_border_color="#2a2a2a",
    button_secondary_border_color_dark="#2a2a2a",
    border_color_primary="#2a2a2a",
    border_color_primary_dark="#2a2a2a",
    shadow_drop="none",
    shadow_drop_lg="none",
    shadow_spread="none",
)


with gr.Blocks(title="Job Application Agent", fill_height=True) as demo:
    gr.Markdown("# Job Application Agent\n*multi-agent · resume tailoring · application answers*")
    gr.Markdown("---")

    with gr.Row(equal_height=True):
        with gr.Column(scale=1, min_width=300):
            url_box  = gr.Textbox(label="Job URL", placeholder="https://company.com/jobs/role", lines=1, max_lines=1)
            cv_box   = gr.File(label="CV Files", file_types=[".pdf", ".txt", ".typ"],
                               file_count="multiple", height=100)
            tpl_file = gr.File(label="Typst Template (optional)", file_types=[".typ", ".txt"],
                               height=100)
            tpl_text = gr.Textbox(label="…or paste template", lines=8, max_lines=8,
                                  placeholder="// Typst template…")
            run_btn  = gr.Button("Run Agent", variant="primary", size="lg")

        with gr.Column(scale=2, min_width=480):
            stage_box = gr.Textbox(label="Stage", value="Ready", interactive=False,
                                   lines=1, max_lines=1)
            logs      = gr.Textbox(label="Agent Log", value="", interactive=False,
                                   lines=24, max_lines=24, autoscroll=True)
            gr.Markdown("---")
            with gr.Row():
                dl_typ    = gr.DownloadButton(label="Resume (.typ)",      value=None, interactive=False, size="sm")
                dl_pdf    = gr.DownloadButton(label="Resume PDF",          value=None, interactive=False, size="sm")
                dl_qa     = gr.DownloadButton(label="Application Answers", value=None, interactive=False, size="sm")
                dl_report = gr.DownloadButton(label="Alignment Report",    value=None, interactive=False, size="sm")

    run_btn.click(fn=start, inputs=[url_box, cv_box, tpl_file, tpl_text], outputs=[logs, stage_box, run_btn])

    timer = gr.Timer(value=1)
    timer.tick(fn=poll_stage,     inputs=[stage_box], outputs=[stage_box, run_btn])
    timer.tick(fn=poll_logs,      inputs=[logs],      outputs=[logs])
    timer.tick(fn=poll_downloads, outputs=[dl_typ, dl_qa, dl_report, dl_pdf])

if __name__ == "__main__":
    demo.launch(theme=theme)
