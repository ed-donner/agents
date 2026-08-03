import gradio as gr
from sidekick import Sidekick
import os

async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick

async def process_message(sidekick, message, success_criteria, history, input_csv_file):
    # Ensure sidekick is initialized
    if sidekick is None:
        sidekick = Sidekick()
        await sidekick.setup()
    # Pass input CSV only if it exists; else None
    input_csv_path = input_csv_file if input_csv_file and os.path.exists(input_csv_file) else None
    print("Input CSV path:", input_csv_file, os.path.exists(input_csv_file))
    # Output folder instead of file
    output_folder = "./.gradio/output"
    os.makedirs(output_folder, exist_ok=True)
    # Run the LLM superstep
    results, output_file = await sidekick.run_superstep(
        message, success_criteria, history, input_csv_path, output_folder
    )
    output_file_path = output_file if output_file and os.path.exists(output_file) else None
    # Return conversation history, sidekick state, and actual output file
    return results, sidekick, output_file_path



async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", [], new_sidekick, "", ""

def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")

with gr.Blocks(title="Sidekick") as demo:
    gr.Markdown("## Sidekick Personal Co-Worker")
    gradio_sidekick_state = gr.State(delete_callback=free_resources)
    with gr.Row():
        with gr.Column(scale=4):
            with gr.Row():
                chatbot = gr.Chatbot(label="Sidekick", height=300)
            with gr.Group():
                with gr.Row():
                    message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
                with gr.Row():
                    success_criteria = gr.Textbox(
                        show_label=False, placeholder="What are your success critiera?"
                    )
            with gr.Row():
                reset_button = gr.Button("Reset", variant="stop")
                go_button = gr.Button("Go!", variant="primary")
        with gr.Column(scale=1):
                with gr.Row():
                    input_csv_file = gr.File(label="CSV file (optional)", file_types=[".csv"],  type="filepath")
                with gr.Row():
                    output_csv_file = gr.File(label="Output CSV file", file_types=[".csv"],  type="filepath")

    demo.load(setup, [], [gradio_sidekick_state])
    go_button.click(
        process_message, [gradio_sidekick_state, message, success_criteria, chatbot, input_csv_file], [chatbot, gradio_sidekick_state, output_csv_file]
    )
    print(message, success_criteria, chatbot, gradio_sidekick_state, input_csv_file, "INPUT")
    reset_button.click(reset, [], [message, success_criteria, chatbot, gradio_sidekick_state, input_csv_file, output_csv_file])

demo.launch(inbrowser=True,
    theme=gr.themes.Default(primary_hue="emerald")
)
