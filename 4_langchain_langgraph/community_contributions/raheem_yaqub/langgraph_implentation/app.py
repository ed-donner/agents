import gradio as gr
import os
from sidekick import Sidekick
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick



async def process_message(sidekick, message, success_criteria, history):
    updated_history, tool_logs = await sidekick.run_superstep(
        message, success_criteria, history
    )

    tool_text = "### 🛠 Tool Execution Logs\n\n"

    for log in tool_logs:
        if "tool" in log:
            tool_text += f"🛠 **Tool:** `{log['tool']}`\n"
            tool_text += f"📥 **Input:** `{log['input']}`\n"
        if "output" in log:
            tool_text += f"📤 **Output:** `{log['output']}`\n\n"

    return updated_history, sidekick, tool_text


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick, ""


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

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")

    with gr.Row():
        tool_logs = gr.Markdown("### 🛠 Tool Execution Logs")

    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False, placeholder="Your request to the Sidekick"
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="What are your success criteria?",
            )

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick])

    message.submit(
        process_message,
        [sidekick, message, success_criteria, chatbot],
        [chatbot, sidekick, tool_logs],
    )

    success_criteria.submit(
        process_message,
        [sidekick, message, success_criteria, chatbot],
        [chatbot, sidekick, tool_logs],
    )

    go_button.click(
        process_message,
        [sidekick, message, success_criteria, chatbot],
        [chatbot, sidekick, tool_logs],
    )

    reset_button.click(
        reset,
        [],
        [message, success_criteria, chatbot, sidekick, tool_logs],
    )


ui.launch(inbrowser=True)