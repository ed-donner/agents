"""Gradio UI for SafePasteManager — same streaming pattern as 2_openai/deep_research/deep_research.py."""

from pathlib import Path

import gradio as gr

from env_setup import load_repo_env

load_repo_env()

from orchestrator import SafePasteManager

_HERE = Path(__file__).resolve().parent


def _sample_choices() -> list[str]:
    d = _HERE / "sample_inputs"
    if not d.is_dir():
        return []
    return sorted(p.name for p in d.glob("*.txt"))


def _load_sample(filename: str) -> str:
    if not filename:
        return ""
    p = _HERE / "sample_inputs" / filename
    if p.is_file():
        return p.read_text(encoding="utf-8")
    return ""


async def stream_output(text: str):
    text = (text or "").strip()
    if not text:
        yield "_Paste text above (or load a sample), then click **Run**._"
        return
    parts: list[str] = []
    async for chunk in SafePasteManager().run(text):
        parts.append(chunk)
        yield "".join(parts)


def build_ui():
    with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as demo:
        gr.Markdown(
            "# Safe public paste\n"
            "Multi-agent scan → redaction guidance or error explanation. "
            "See `README.md` for limitations."
        )
        sample_dd = gr.Dropdown(
            label="Load sample (optional)",
            choices=_sample_choices(),
            value=None,
        )
        inp = gr.Textbox(
            label="Paste logs, stack traces, or HTTP snippets",
            lines=14,
            placeholder="Paste here…",
        )
        sample_dd.change(fn=_load_sample, inputs=sample_dd, outputs=inp)
        run_btn = gr.Button("Run", variant="primary")
        out = gr.Markdown(label="Result")
        run_btn.click(fn=stream_output, inputs=inp, outputs=out)
        inp.submit(fn=stream_output, inputs=inp, outputs=out)
    return demo


def main():
    build_ui().launch(inbrowser=True)


if __name__ == "__main__":
    main()
