from __future__ import annotations

import gradio as gr
import nest_asyncio
from dotenv import load_dotenv

nest_asyncio.apply()
load_dotenv(override=True)

from job_hunt_assistant import JobHuntAssistant


async def init_assistant() -> JobHuntAssistant:
    bot = JobHuntAssistant()
    await bot.setup()
    return bot


async def process_turn(
    assistant: JobHuntAssistant,
    request: str,
    job_context: str,
    criteria: str,
    history: list,
):
    if not request.strip():
        return history, assistant
    criteria_final = (criteria or "").strip() or (
        "Summarize findings clearly; match any stated JD keywords; "
        "save a markdown package if a draft or summary was requested; "
        "do not invent salary, deadlines, or requirements."
    )
    context_block = (job_context or "").strip()
    if context_block:
        user_text = f"[Profile / targets]\n{context_block}\n\n[Request]\n{request.strip()}"
    else:
        user_text = request.strip()
    updated = await assistant.run_superstep(user_text, criteria_final, history)
    return updated, assistant


async def reset_session():
    new_bot = JobHuntAssistant()
    await new_bot.setup()
    return "", "", "", None, new_bot


async def on_load():
    return await init_assistant()


def free_resources(assistant: JobHuntAssistant | None):
    if assistant:
        try:
            assistant.cleanup()
        except Exception as e:  # noqa: BLE001
            print(f"Cleanup: {e}")


with gr.Blocks(
    title="Job Hunt Assistant",
    theme=gr.themes.Default(primary_hue="blue"),
) as demo:
    gr.Markdown(
        "## Job Hunt Assistant (LangGraph)\n"
        "Research roles, summarize JDs, draft outreach — with **SQLite checkpointing**, **tools**, "
        "optional **Playwright** browser tools, and an **evaluator**."
    )
    assistant_state = gr.State(delete_callback=free_resources)

    with gr.Row():
        chat = gr.Chatbot(label="Chat", height=380, type="messages")
    profile = gr.Textbox(
        label="Profile / targets (role, location, stack, links)",
        placeholder="e.g. Senior Python, remote EU, 6y backend; LinkedIn …",
        lines=3,
    )
    request = gr.Textbox(
        label="What do you want this turn?",
        placeholder="e.g. Summarize this posting and suggest 5 resume bullets …",
        lines=2,
    )
    criteria = gr.Textbox(
        label="Success criteria (evaluator uses this)",
        placeholder="e.g. Must cite JD requirements; save package as acme_sre.md; no invented salary.",
        lines=2,
    )
    with gr.Row():
        reset_btn = gr.Button("New session", variant="stop")
        go_btn = gr.Button("Run", variant="primary")

    demo.load(on_load, [], [assistant_state])

    go_btn.click(
        process_turn,
        [assistant_state, request, profile, criteria, chat],
        [chat, assistant_state],
    )
    request.submit(
        process_turn,
        [assistant_state, request, profile, criteria, chat],
        [chat, assistant_state],
    )

    reset_btn.click(
        reset_session,
        [],
        [profile, request, criteria, chat, assistant_state],
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True)
