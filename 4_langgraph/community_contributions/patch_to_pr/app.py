"""Gradio UI: paste a patch, get PR title + body with evaluator loop (LangGraph)."""

from __future__ import annotations

import uuid
import gradio as gr
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from sidekick import DEFAULT_SUCCESS_CRITERIA, build_graph

load_dotenv(override=True)

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def make_thread_id() -> str:
    return str(uuid.uuid4())


def _build_user_message(patch: str, extra_context: str) -> str:
    patch = (patch or "").strip()
    extra = (extra_context or "").strip()
    parts = ["Here is the git patch / diff to turn into a pull request:\n\n```diff\n", patch, "\n```"]
    if extra:
        parts.extend(["\n\nAdditional context from the author:\n", extra])
    return "".join(parts)


async def process_message(
    patch: str,
    extra_context: str,
    success_criteria: str,
    history: list,
):
    patch = (patch or "").strip()
    if not patch:
        user = {"role": "user", "content": "(empty patch)"}
        reply = {
            "role": "assistant",
            "content": "Paste a `git diff` or patch first, then click **Generate**.",
        }
        return history + [user, reply]

    # Fresh thread per run so checkpoint state does not stack unrelated patches.
    config = {"configurable": {"thread_id": make_thread_id()}}

    criteria = (success_criteria or "").strip() or DEFAULT_SUCCESS_CRITERIA
    user_text = _build_user_message(patch, extra_context)

    state = {
        "messages": [HumanMessage(content=user_text)],
        "success_criteria": criteria,
        "feedback_on_work": None,
        "success_criteria_met": False,
        "user_input_needed": False,
        "eval_round": 0,
    }

    result = await get_graph().ainvoke(state, config=config)
    messages = result["messages"]
    user = {"role": "user", "content": user_text}
    if len(messages) >= 2:
        draft = messages[-2]
        feedback = messages[-1]
        draft_text = getattr(draft, "content", None) or str(draft)
        feedback_text = getattr(feedback, "content", None) or str(feedback)
        reply = {"role": "assistant", "content": draft_text}
        fb = {"role": "assistant", "content": feedback_text}
        return history + [user, reply, fb]

    last = messages[-1] if messages else None
    text = getattr(last, "content", None) or str(last) if last else "No output."
    return history + [user, {"role": "assistant", "content": text}]


async def reset():
    return "", "", DEFAULT_SUCCESS_CRITERIA, None


with gr.Blocks(title="Patch → PR", theme=gr.themes.Default(primary_hue="emerald")) as demo:
    gr.Markdown(
        "## Patch → PR (LangGraph)\n"
        "Paste a **`git diff`** (or patch). A **drafter** model writes PR Markdown; an **evaluator** checks it against "
        "your success criteria and may request revisions (up to a small cap). Uses **`OPENAI_API_KEY`** and `gpt-4o-mini` by default. "
        "Each run uses a new LangGraph thread id so checkpoints do not mix unrelated patches."
    )

    patch_in = gr.Textbox(
        label="Patch / diff",
        placeholder="git diff output or unified diff…",
        lines=14,
    )
    context_in = gr.Textbox(
        label="Optional context",
        placeholder="Ticket link, repo name, intent, reviewers to mention…",
        lines=3,
    )
    criteria_in = gr.Textbox(
        label="Success criteria (optional; defaults to built-in checklist)",
        value=DEFAULT_SUCCESS_CRITERIA,
        lines=8,
    )

    with gr.Row():
        chatbot = gr.Chatbot(label="Result", height=420, type="messages")
    with gr.Row():
        reset_btn = gr.Button("Reset", variant="stop")
        go_btn = gr.Button("Generate PR draft", variant="primary")

    go_btn.click(
        process_message,
        [patch_in, context_in, criteria_in, chatbot],
        [chatbot],
    )
    reset_btn.click(reset, [], [patch_in, context_in, criteria_in, chatbot])


if __name__ == "__main__":
    demo.launch(inbrowser=True)
