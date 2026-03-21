import gradio as gr
from dotenv import load_dotenv
from agents import Runner
from research_manager import ResearchManager
from clarifier_agent import clarifier_agent

load_dotenv(override=True)


def format_conversation(history: list[list[str]]) -> str:
    """Format chat history for the clarifier agent."""
    lines = []
    for user_msg, assistant_msg in history:
        if user_msg:
            lines.append(f"User: {user_msg}")
        if assistant_msg:
            lines.append(f"Assistant: {assistant_msg}")
    return "\n".join(lines) if lines else "No prior messages."


async def chat_turn(message: str, history: list[list[str]], refined_query: str):
    """Handle one user message: run clarifier, return updated history and refined_query."""
    if not message or not message.strip():
        return history, refined_query, gr.update(interactive=True)

    conv = format_conversation(history)
    prompt = f"Conversation so far:\n{conv}\n\nLatest user message: {message}"
    result = await Runner.run(clarifier_agent, prompt)
    out = result.final_output

    new_refined = out.refined_query if out.ready_to_research else refined_query
    new_history = history + [[message, out.message]]

    start_btn = gr.update(interactive=bool(new_refined.strip()))
    return new_history, new_refined, start_btn


async def run_research(refined_query: str):
    """Run the full research pipeline and stream output. Disables Send/Start research while running."""
    disabled = gr.update(interactive=False)
    enabled = gr.update(interactive=True)
    if not refined_query or not refined_query.strip():
        yield "Please use the chat above to clarify your research topic first. Once the assistant confirms readiness, click **Start research**.", enabled, enabled
        return
    report_so_far = ""
    async for chunk in ResearchManager().run(refined_query):
        report_so_far += chunk
        yield report_so_far, disabled, disabled
    yield report_so_far, enabled, enabled


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky"), title="Deep Research") as ui:
    gr.Markdown("# Deep Research")
    gr.Markdown("Chat to clarify your topic, then click **Start research** when ready.")

    chat = gr.Chatbot(label="Clarify your topic", height=400)
    msg = gr.Textbox(
        label="Message",
        placeholder="Describe what you want to research or answer the assistant's questions...",
        show_label=False,
    )
    submit_btn = gr.Button("Send", variant="secondary")
    start_research_btn = gr.Button("Start research", variant="primary", interactive=False)
    new_research_btn = gr.Button("New research", variant="secondary")

    report = gr.Markdown(label="Report")

    refined_query_state = gr.State(value="")

    async def on_send(message, history, refined_query):
        new_history, new_refined, start_btn = await chat_turn(message, history, refined_query)
        return new_history, new_refined, start_btn

    submit_btn.click(
        fn=on_send,
        inputs=[msg, chat, refined_query_state],
        outputs=[chat, refined_query_state, start_research_btn],
    ).then(fn=lambda: "", outputs=msg)
    msg.submit(
        fn=on_send,
        inputs=[msg, chat, refined_query_state],
        outputs=[chat, refined_query_state, start_research_btn],
    ).then(fn=lambda: "", outputs=msg)

    start_research_btn.click(
        fn=run_research,
        inputs=refined_query_state,
        outputs=[report, submit_btn, start_research_btn],
    )

    def on_new_research():
        """Clear chat, report, and refined query; disable Start research."""
        return (
            [],  # chat
            "",  # msg
            "",  # report
            "",  # refined_query_state
            gr.update(interactive=False),  # start_research_btn
        )

    new_research_btn.click(
        fn=on_new_research,
        inputs=[],
        outputs=[chat, msg, report, refined_query_state, start_research_btn],
    )

ui.launch(inbrowser=True)
