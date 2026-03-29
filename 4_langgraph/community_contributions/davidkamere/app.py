import gradio as gr
from sidekick import ClientDiscoverySidekick


async def setup():
    sidekick = ClientDiscoverySidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset():
    new_sidekick = ClientDiscoverySidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick


with gr.Blocks(title="Client Discovery Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Client Discovery Sidekick")
    gr.Markdown("A LangGraph co-worker for researching companies, preparing discovery briefs, and saving memory in SQLite.")
    sidekick = gr.State()

    chatbot = gr.Chatbot(label="Sidekick", height=420, type="messages")
    with gr.Row():
        message = gr.Textbox(show_label=False, placeholder="Example: Research Stripe for outreach prep and create a discovery brief")
    with gr.Row():
        success_criteria = gr.Textbox(
            show_label=False,
            placeholder="Example: I want a concise brief with product summary, recent developments, likely needs, and outreach angles.",
        )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    gr.Examples(
        examples=[
            ["Research Stripe for outreach prep and create a discovery brief", "Summarize what they do, recent developments, possible technical needs, and 3 outreach angles."],
            ["Prepare interview notes for Deloitte as a potential client/company", "Give me a client-style brief with company overview, product context, and useful talking points."],
            ["Research a healthcare startup for discovery call prep", "Ask clarifying questions first if the company is missing, then produce a practical brief."],
        ],
        inputs=[message, success_criteria],
    )

    ui.load(setup, [], [sidekick])
    message.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    success_criteria.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    go_button.click(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])

ui.launch(inbrowser=True)
