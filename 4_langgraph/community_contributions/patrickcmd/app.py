import gradio as gr
from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_go(sidekick, message, success_criteria, history, phase, stored_questions, original_message):
    if phase == "initial":
        questions = sidekick.generate_clarifying_questions(message)
        q_list = [questions.question_1, questions.question_2, questions.question_3]
        history = (history or []) + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": (
                "Before I begin, I have a few clarifying questions:\n\n"
                f"1. {q_list[0]}\n"
                f"2. {q_list[1]}\n"
                f"3. {q_list[2]}\n\n"
                "Please type your answers below and click Go! again."
            )},
        ]
        return history, sidekick, "clarifying", q_list, message, gr.update(value="")

    else:
        history = (history or []) + [
            {"role": "user", "content": message},
        ]
        refined = sidekick.refine_prompt(original_message, stored_questions, [message])
        results = await sidekick.run_superstep(refined, success_criteria, history)
        return results, sidekick, "initial", [], "", gr.update(value="")


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick, "initial", [], ""


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
    phase = gr.State("initial")
    stored_questions = gr.State([])
    original_message = gr.State("")

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300)
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success criteria?"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick])

    go_inputs = [sidekick, message, success_criteria, chatbot, phase, stored_questions, original_message]
    go_outputs = [chatbot, sidekick, phase, stored_questions, original_message, message]

    go_button.click(process_go, go_inputs, go_outputs)
    message.submit(process_go, go_inputs, go_outputs)
    reset_button.click(
        reset,
        [],
        [message, success_criteria, chatbot, sidekick, phase, stored_questions, original_message],
    )


ui.launch(inbrowser=True)