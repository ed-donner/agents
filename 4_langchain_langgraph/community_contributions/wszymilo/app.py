"""
Gradio UI for the LangGraph deep-research pipeline. Includes HITL handling.
"""
import uuid
from typing import Any

import gradio as gr
from dotenv import find_dotenv, load_dotenv
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command


load_dotenv(find_dotenv())

from research_graph import (
    EvaluationResult,
    GraphState,
    MEMORY_DB_PATH,
    Report,
    build_graph,
    send_pushover_completion_notice,
)

def _unwrap_interrupt(out: dict[str, Any]) -> Any | None:
    """Return the payload LangGraph attached when the run paused on `interrupt()`, or None.

    `ainvoke` exposes pauses as `out["__interrupt__"]`, often a sequence of objects whose
    `.value` holds what was passed to `interrupt(...)` (here `{"question": ...}`). This
    helper normalizes that to a single value for the UI.
    """
    raw = out.get("__interrupt__")
    if not raw:
        return None
    first = raw[0] if isinstance(raw, (list, tuple)) else raw
    return getattr(first, "value", first)


def _format_result_markdown(out: dict[str, Any]) -> str:
    """Turn graph `ainvoke` output into one Markdown string for the single `gr.Markdown` sink.

    Covers: human-in-the-loop clarification (interrupt), triage abort, evaluator pass/fail, success, 
    and a generic fallback.
    """
    intr_val = _unwrap_interrupt(out)
    if intr_val is not None:
        q = (
            str(intr_val.get("question", ""))
            if isinstance(intr_val, dict)
            else str(intr_val)
        )
        return (
            "## Clarification needed\n\n"
            "Answer in the text box below and submit again (same session).\n\n"
            f"**Question:** {q}"
        )

    term = out.get("terminal_outcome")
    rep = out.get("report")
    ev = out.get("last_eval")

    if term == "triage_abort":
        return (
            "## Stopped\n\n"
            "Triage ended without a clear query: too many ambiguous rounds "
            "without enough clarification."
        )

    if term == "eval_fail" and isinstance(rep, Report) and isinstance(ev, EvaluationResult):
        gaps = "\n".join(f"- {g}" for g in ev.gaps) or "(none listed)"
        sugg = "\n".join(f"- `{s}`" for s in ev.suggested_searches) or "(none)"
        return (
            "## Report (last draft)\n\n"
            f"{rep.markdown_report}\n\n"
            "## Evaluator feedback\n\n"
            f"**Passes:** {ev.passes}\n\n"
            f"**Gaps:**\n{gaps}\n\n"
            f"**Suggested searches:**\n{sugg}"
        )

    if isinstance(rep, Report):
        body = f"## Report\n\n{rep.markdown_report}"
        if term == "success":
            body += f"\n\n**Summary:** {rep.summary}"
        return body

    return f"## Result\n\n```\n{out}\n```"


async def on_submit(
    user_input: str,
    thread_id: str | None,
    awaiting_resume: bool,
    enable_pushover: bool,
) -> tuple[str, str | None, bool, str]:
    text = user_input.strip()
    if not text:
        return (
            "## Error\n\nEnter a question or a clarification answer.",
            thread_id,
            awaiting_resume,
            "",
        )

    thread_id = str(uuid.uuid4()) if thread_id is None else thread_id

    cfg: dict[str, Any] = {"configurable": {"thread_id": thread_id}}

    try:
        async with AsyncSqliteSaver.from_conn_string(str(MEMORY_DB_PATH)) as saver:
            graph = build_graph(saver)
            if awaiting_resume:
                out = await graph.ainvoke(Command(resume=text), cfg)
            else:
                init: GraphState = {
                    "query": text,
                    "user_clarifications": "",
                    "round_idx": 0,
                }
                out = await graph.ainvoke(init, cfg)
    except Exception as e:
        return (
            f"## Error\n\n{type(e).__name__}: {e}",
            thread_id,
            awaiting_resume,
            "",
        )

    if out.get("__interrupt__"):
        return _format_result_markdown(out), thread_id, True, ""

    term = out.get("terminal_outcome")

    if enable_pushover and term == "success":
        send_pushover_completion_notice()

    md = _format_result_markdown(out)
    reset_thread = term in ("success", "eval_fail", "triage_abort")
    return md, (None if reset_thread else thread_id), False, ""


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Deep research (LangGraph)") as demo:
        gr.Markdown(
            "Deep research pipeline: triage -> plan -> research -> report -> evaluate. "
            "If the model asks for clarification, answer in the same box and submit again. "
            "After a finished run, the next message starts a **new** thread. "
            "Checkpoint DB: `data/memory.db`."
        )
        out_md = gr.Markdown("Submit a research question to begin.")
        inp = gr.Textbox(
            label="Question or clarification",
            lines=4,
            placeholder="e.g. What is Banoffee pie and how many calories does a slice have?",
        )
        thread_st = gr.State(None)
        paused_st = gr.State(False)
        pushover_cb = gr.Checkbox(
            label="Send Pushover notification when the evaluator passes",
            value=True,
        )
        gr.Button("Submit").click(
            fn=on_submit,
            inputs=[inp, thread_st, paused_st, pushover_cb],
            outputs=[out_md, thread_st, paused_st, inp],
        )
    return demo


if __name__ == "__main__":
    build_ui().launch(server_name="127.0.0.1", server_port=7860)
