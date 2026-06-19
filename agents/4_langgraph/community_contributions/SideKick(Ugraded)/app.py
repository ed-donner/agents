import os
from dotenv import load_dotenv
load_dotenv(override=True)

import gradio as gr
from sidekick_tools import create_calendar_event, list_upcoming_events
from sidekick import Sidekick

async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick

async def process_message(sidekick, message, success_criteria, history):
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick

async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")

# Gradio UI
with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(show_label=False, placeholder="What are your success criteria?")
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    # Calendar Accordion
    with gr.Accordion("📆 Calendar", open=False):
        cal_summary     = gr.Textbox(label="Event Title")
        cal_start       = gr.Textbox(label="Start (RFC3339)", placeholder="2025-05-20T15:00:00+05:30")
        cal_end         = gr.Textbox(label="End   (RFC3339)", placeholder="2025-05-20T16:00:00+05:30")
        cal_description = gr.Textbox(label="Description (optional)")
        add_event_btn   = gr.Button("Add Event")
        list_events_btn = gr.Button("List Upcoming Events")
        cal_output      = gr.Textbox(label="Calendar Output", interactive=False)

    # Bind main functions
    ui.load(setup, [], [sidekick])
    message.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    success_criteria.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    go_button.click(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])

    # Bind calendar tools
    add_event_btn.click(
        fn=lambda summary, start, end, desc: create_calendar_event(
            summary, start, end, desc, os.getenv("GOOGLE_CALENDAR_ID", "primary")
        ),
        inputs=[cal_summary, cal_start, cal_end, cal_description],
        outputs=cal_output
    )
    list_events_btn.click(
        fn=lambda: list_upcoming_events(os.getenv("GOOGLE_CALENDAR_ID", "primary")),
        outputs=cal_output
    )

ui.launch(inbrowser=True)