import gradio as gr
from sidekick import Sidekick


async def setup(username: str):
    sidekick = Sidekick()
    await sidekick.setup()
    sidekick.set_username(username or "guest")
    return sidekick


async def fetch_clarifications(sidekick, message: str, success_criteria: str):
    if not (message or "").strip():
        return gr.update(value="Enter a request first."), None, "", "", ""
    try:
        out = await sidekick.propose_clarifications(message, success_criteria)
        qs = list(out.questions)
        if len(qs) != 3:
            return (
                gr.update(value="Model did not return three questions; try again."),
                None,
                "",
                "",
                "",
            )
        md = "### Clarifying questions\n\n" + "\n\n".join(f"**{i + 1}.** {q}" for i, q in enumerate(qs))
        return gr.update(value=md), qs, "", "", ""
    except Exception as e:
        return gr.update(value=f"Error: {e}"), None, "", "", ""


async def process_message(
    sidekick,
    username: str,
    message: str,
    success_criteria: str,
    answer_1: str,
    answer_2: str,
    answer_3: str,
    stored_questions,
    history,
):
    sidekick.set_username(username or "guest")
    answers = [(answer_1 or "").strip(), (answer_2 or "").strip(), (answer_3 or "").strip()]
    hist = history or []

    if stored_questions and len(stored_questions) == 3:
        if not all(answers):
            bump = hist + [{"role": "assistant", "content": "Please answer all three questions before running."}]
            return bump, stored_questions, gr.update(), gr.update(), gr.update(), gr.update()
    else:
        decision = await sidekick.assess_clarification_need(message, success_criteria)
        if decision.requires_clarification:
            qs = list(decision.questions)
            md = "### Clarifying questions required\n\n" + "\n\n".join(
                f"**{i + 1}.** {q}" for i, q in enumerate(qs)
            )
            prompt = decision.rationale or "This request needs clarification before execution."
            bump = hist + [{"role": "assistant", "content": prompt}]
            return bump, qs, gr.update(value=md), "", "", ""
        stored_questions = None
        answers = None
    try:
        results = await sidekick.run_superstep(
            message,
            success_criteria,
            history,
            stored_questions,
            answers,
            username or "guest",
        )
        return results, None, gr.update(value=""), "", "", ""
    except ValueError as e:
        bump = (history or []) + [{"role": "assistant", "content": str(e)}]
        return bump, stored_questions, gr.update(), gr.update(), gr.update(), gr.update()
    except Exception as e:
        bump = (history or []) + [{"role": "assistant", "content": f"Run failed: {e}"}]
        return bump, stored_questions, gr.update(), gr.update(), gr.update(), gr.update()


async def reset(username: str):
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    new_sidekick.set_username(username or "guest")
    return (
        "",
        "",
        "",
        "",
        "",
        None,
        gr.update(value=""),
        new_sidekick,
        gr.update(value=[]),
    )


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown(
        "## Sidekick Personal Co-Worker\n"
        "Set a **username** so SQLite checkpoint memory and your **task library** persist when you return. "
        "Simple requests can run immediately. More complex or ambiguous requests will require **3 clarifying answers** before execution. "
        "A **planner** delegates steps to **research**, **browser**, **files**, and **BEC** (domain posture) specialists before an **integrator** answers."
    )
    sidekick = gr.State(delete_callback=free_resources)
    clarifying_questions = gr.State(value=None)

    with gr.Row():
        username = gr.Textbox(
            label="Username (memory thread + task library)",
            value="guest",
            scale=1,
        )
    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=360)
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick", scale=2)
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Success criteria — what does ‘done’ look like?",
                scale=2,
            )
    clarifications_md = gr.Markdown("")
    with gr.Row():
        answer_1 = gr.Textbox(label="Answer 1", placeholder="Answer to question 1")
        answer_2 = gr.Textbox(label="Answer 2", placeholder="Answer to question 2")
        answer_3 = gr.Textbox(label="Answer 3", placeholder="Answer to question 3")
    with gr.Row():
        clarify_btn = gr.Button("Get clarifying questions", variant="secondary")
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [username], [sidekick])

    clarify_btn.click(
        fetch_clarifications,
        [sidekick, message, success_criteria],
        [clarifications_md, clarifying_questions, answer_1, answer_2, answer_3],
    )

    go_button.click(
        process_message,
        [
            sidekick,
            username,
            message,
            success_criteria,
            answer_1,
            answer_2,
            answer_3,
            clarifying_questions,
            chatbot,
        ],
        [chatbot, clarifying_questions, clarifications_md, answer_1, answer_2, answer_3],
    )
    msg_inputs = [
        sidekick,
        username,
        message,
        success_criteria,
        answer_1,
        answer_2,
        answer_3,
        clarifying_questions,
        chatbot,
    ]
    message.submit(
        process_message,
        msg_inputs,
        [chatbot, clarifying_questions, clarifications_md, answer_1, answer_2, answer_3],
    )
    success_criteria.submit(
        process_message,
        msg_inputs,
        [chatbot, clarifying_questions, clarifications_md, answer_1, answer_2, answer_3],
    )

    reset_button.click(
        reset,
        [username],
        [
            message,
            success_criteria,
            answer_1,
            answer_2,
            answer_3,
            clarifying_questions,
            clarifications_md,
            sidekick,
            chatbot,
        ],
    )


ui.launch(inbrowser=True)
