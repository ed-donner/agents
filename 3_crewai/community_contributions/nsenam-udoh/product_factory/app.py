import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
import threading

import gradio as gr

from product_factory.flow import DEFAULT_REQUIREMENTS, run_flow
from product_factory.tools.sandbox_reset import (
    reset_workstream,
    validate_workstream_id,
    workstream_root,
)


CSS = """
:root {
  --pf-bg: #f3f5f1;
  --pf-surface: #ffffff;
  --pf-text: #17211c;
  --pf-muted: #4b5b51;
  --pf-border: #bac5bc;
  --pf-accent: #185c37;
  --pf-accent-text: #ffffff;
  --pf-danger: #9d2525;
  --pf-focus: #246b45;
}
.dark {
  --pf-bg: #111713;
  --pf-surface: #19221c;
  --pf-text: #edf4ef;
  --pf-muted: #b8c8bd;
  --pf-border: #53665a;
  --pf-accent: #93d7aa;
  --pf-accent-text: #102117;
  --pf-danger: #ffaaaa;
  --pf-focus: #b4e7c5;
}
.gradio-container {
  max-width: 860px !important;
  margin: 0 auto !important;
  padding: 28px 20px 48px !important;
  background: var(--pf-bg) !important;
  color: var(--pf-text) !important;
  font-family: ui-sans-serif, system-ui, sans-serif !important;
}
.gradio-container .block, .gradio-container .form {
  background: var(--pf-surface) !important;
  border-color: var(--pf-border) !important;
  border-radius: 12px !important;
  box-shadow: none !important;
}
.gradio-container label, .gradio-container .label-wrap span {
  color: var(--pf-text) !important;
  font-weight: 650 !important;
}
.gradio-container input:not([type="checkbox"]):not([type="radio"]),
.gradio-container textarea {
  background: var(--pf-surface) !important;
  color: var(--pf-text) !important;
  caret-color: var(--pf-accent) !important;
}
.gradio-container input::placeholder, .gradio-container textarea::placeholder {
  color: var(--pf-muted) !important;
  opacity: 1 !important;
}
/* Keep native checkbox marks visible; generic input CSS hides them. */
.gradio-container input[type="checkbox"] {
  -webkit-appearance: checkbox !important;
  appearance: auto !important;
  width: 1.1rem !important;
  height: 1.1rem !important;
  min-width: 1.1rem !important;
  min-height: 1.1rem !important;
  margin: 0 0.5rem 0 0 !important;
  accent-color: var(--pf-accent) !important;
  background-color: #ffffff !important;
  color: var(--pf-accent) !important;
  opacity: 1 !important;
  cursor: pointer !important;
}
.gradio-container .pf-confirm {
  display: flex !important;
  align-items: center !important;
  gap: 0.35rem !important;
}
.gradio-container button.primary {
  background: var(--pf-accent) !important;
  color: var(--pf-accent-text) !important;
  border: 1px solid var(--pf-accent) !important;
}
.gradio-container button.stop {
  color: var(--pf-danger) !important;
  border: 1px solid var(--pf-danger) !important;
  background: var(--pf-surface) !important;
}
.gradio-container button:focus-visible,
.gradio-container input:focus-visible,
.gradio-container textarea:focus-visible {
  outline: 3px solid var(--pf-focus) !important;
  outline-offset: 2px !important;
}
.gradio-container ::selection {
  background: var(--pf-accent) !important;
  color: var(--pf-accent-text) !important;
}
.pf-actions { gap: 12px !important; flex-wrap: wrap !important; }
.pf-actions button { min-height: 44px; flex: 1 1 190px; }
@media (max-width: 600px) {
  .gradio-container { padding: 18px 12px 32px !important; }
  .pf-actions { flex-direction: column !important; }
  .pf-actions button { width: 100% !important; }
}
"""

_JOB = {
    "running": False,
    "status": "Ready.",
    "log": "No build has run yet.",
    "trace_url": None,
}
_JOB_LOCK = threading.Lock()


def _trace_markdown(url: str | None) -> str:
    return f"[Open trace]({url})" if url else "No trace link available yet."


def _snapshot() -> tuple[str, str, str]:
    with _JOB_LOCK:
        return _JOB["status"], _JOB["log"], _trace_markdown(_JOB["trace_url"])


def _set_job(**updates) -> None:
    with _JOB_LOCK:
        _JOB.update(updates)


def _worker(workstream_id: str, requirements: str, feedback: str) -> None:
    try:
        result = run_flow(workstream_id, requirements, feedback)
        verdict = result["verdicts"].get(workstream_id, {})
        _set_job(
            running=False,
            status=f"Build status: {verdict.get('status', 'complete')}.",
            log=json.dumps(result, indent=2),
            trace_url=result.get("trace_link"),
        )
    except Exception as exc:
        _set_job(
            running=False,
            status=f"Build failed: {exc}",
            log=f"{type(exc).__name__}: {exc}",
            trace_url=None,
        )


def _start_build(
    workstream_id: str, requirements: str, feedback: str = ""
) -> tuple[str, str, str]:
    with _JOB_LOCK:
        if _JOB["running"]:
            return _JOB["status"], _JOB["log"], _trace_markdown(_JOB["trace_url"])
    try:
        validate_workstream_id(workstream_id)
    except ValueError as exc:
        return str(exc), _snapshot()[1], _snapshot()[2]
    if not requirements.strip():
        return "Requirements cannot be empty.", _snapshot()[1], _snapshot()[2]
    _set_job(
        running=True,
        status=f"Running build for {workstream_id}...",
        log="The build is running. Status updates automatically.",
        trace_url=None,
    )
    thread = threading.Thread(
        target=_worker,
        args=(workstream_id, requirements, feedback),
        daemon=True,
    )
    thread.start()
    return _snapshot()


def _continue_build(
    workstream_id: str, requirements: str, feedback: str
) -> tuple[str, str, str]:
    if not feedback.strip():
        return "Enter feedback before continuing.", _snapshot()[1], _snapshot()[2]
    return _start_build(workstream_id, requirements, feedback)


def _reset(workstream_id: str, confirmed: bool) -> tuple[str, str, str]:
    # Persist status in _JOB so the 1s timer does not wipe short-lived messages.
    if not confirmed:
        _set_job(
            status="Reset not run. Tick **This deletes sandbox files** first, then click Reset sandbox."
        )
        return _snapshot()
    with _JOB_LOCK:
        running = _JOB["running"]
    if running:
        _set_job(status="Wait for the running build to finish before resetting.")
        return _snapshot()
    try:
        reset_workstream(workstream_root(workstream_id))
    except (OSError, RuntimeError, ValueError) as exc:
        _set_job(status=f"Reset failed: {exc}")
        return _snapshot()
    _set_job(
        status=f"Sandbox {workstream_id} reset.",
        log="The workstream was recreated as a fresh uv project with gradio.",
        trace_url=None,
    )
    return _snapshot()


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Product Factory") as demo:
        workstream = gr.Textbox(label="Workstream id", value="main", max_lines=1)
        requirements = gr.Textbox(
            label="Requirements", value=DEFAULT_REQUIREMENTS, lines=8
        )
        run_button = gr.Button("Run build", variant="primary")
        feedback = gr.Textbox(label="Feedback for next round", lines=4)
        confirm = gr.Checkbox(
            label="This deletes sandbox files",
            value=False,
            interactive=True,
            elem_classes=["pf-confirm"],
            info="Must be checked before Reset sandbox will wipe sandbox/main.",
        )
        with gr.Row(elem_classes=["pf-actions"]):
            continue_button = gr.Button("Continue with feedback")
            reset_button = gr.Button("Reset sandbox", variant="stop")
        status = gr.Markdown("Ready.")
        log = gr.Textbox(label="Run log", value="No build has run yet.", lines=12, interactive=False)
        trace = gr.Markdown("No trace link available yet.")
        timer = gr.Timer(1)
        outputs = [status, log, trace]
        run_button.click(_start_build, [workstream, requirements], outputs)
        continue_button.click(
            _continue_build, [workstream, requirements, feedback], outputs
        )
        reset_button.click(_reset, [workstream, confirm], outputs)
        timer.tick(_snapshot, outputs=outputs)
    return demo


demo = build_ui()


if __name__ == "__main__":
    demo.launch(css=CSS)
