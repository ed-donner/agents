import gradio as gr

from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def fetch_clarifying_questions(sidekick, message: str, success_criteria: str):
    if not message or not message.strip():
        return (
            "*Enter a request and success criteria, then click **Get clarifying questions**.*",
            [],
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
        )
    qs = await sidekick.propose_clarifications(message.strip(), success_criteria or "")
    md = "### Answer these before clicking Go!\n\n" + "\n\n".join(
        f"**{i}.** {q}" for i, q in enumerate(qs.questions, start=1)
    )
    return (
        md,
        qs.questions,
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
    )


async def process_message(sidekick, message, success_criteria, history, questions_state, a1, a2, a3):
    if not questions_state or len(questions_state) != 3:
        return (
            history
            + [
                {
                    "role": "assistant",
                    "content": "Use **Get clarifying questions** first, then answer all three before **Go!**.",
                }
            ],
            sidekick,
        )
    if not a1.strip() or not a2.strip() or not a3.strip():
        return (
            history
            + [{"role": "assistant", "content": "Please answer all three clarifying questions before **Go!**."}],
            sidekick,
        )
    results = await sidekick.run_superstep(
        message,
        success_criteria,
        history,
        clarifying_questions=questions_state,
        answers=[a1.strip(), a2.strip(), a3.strip()],
    )
    return results, sidekick


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return (
        "",
        "",
        None,
        new_sidekick,
        "*Click **Get clarifying questions** after describing your task.*",
        [],
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    sidekick = gr.State(delete_callback=free_resources)
    questions_state = gr.State([])

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success criteria?"
            )
    clarify_btn = gr.Button("Get clarifying questions", variant="secondary")
    questions_md = gr.Markdown("*The assistant will propose three questions here.*")

    gr.Markdown("### Your answers")
    a1 = gr.Textbox(label="Answer to question 1", visible=False)
    a2 = gr.Textbox(label="Answer to question 2", visible=False)
    a3 = gr.Textbox(label="Answer to question 3", visible=False)

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary", visible=False)

    ui.load(setup, [], [sidekick])
    clarify_btn.click(
        fetch_clarifying_questions,
        [sidekick, message, success_criteria],
        [questions_md, questions_state, a1, a2, a3, go_button],
    )
    message.submit(
        process_message,
        [sidekick, message, success_criteria, chatbot, questions_state, a1, a2, a3],
        [chatbot, sidekick],
    )
    success_criteria.submit(
        process_message,
        [sidekick, message, success_criteria, chatbot, questions_state, a1, a2, a3],
        [chatbot, sidekick],
    )
    go_button.click(
        process_message,
        [sidekick, message, success_criteria, chatbot, questions_state, a1, a2, a3],
        [chatbot, sidekick],
    )
    reset_button.click(
        reset,
        [],
        [
            message,
            success_criteria,
            chatbot,
            sidekick,
            questions_md,
            questions_state,
            a1,
            a2,
            a3,
            go_button,
        ],
    )


ui.launch(inbrowser=True)
