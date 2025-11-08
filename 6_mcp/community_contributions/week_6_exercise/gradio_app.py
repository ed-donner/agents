import gradio as gr
import nest_asyncio
from datetime import datetime
from process_request import process_user_request

nest_asyncio.apply()

async def run_pipeline_async(user_input, session_state):
    state = session_state or {"history": [], "clarifier_state": None}
    history = state.get("history", [])
    clarifier_state = state.get("clarifier_state")
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": "Processing..."})

    try:
        pdf_path, data = await process_user_request(user_input, clarifier_state)
        if data.get("status") == "clarifying":
            clarifier_reply = data["clarifier_reply"]
            new_state = data["clarifier_state"]

            message = (
                f"**Clarification question {new_state['round'] - 1}**\n\n"
                f"{clarifier_reply}\n\n"
            )

            history[-1] = {"role": "assistant", "content": message}
            return {"history": history, "clarifier_state": new_state}, None

        elif data.get("status") == "done":
            message = (
                f" **your question is clear now.**\n\n"
                f" *Your report is being finalized, be patient.*"
            )
            history[-1] = {"role": "assistant", "content": message}
            return {"history": history, "clarifier_state": None}, pdf_path

    except Exception as e:
        history[-1] = {"role": "assistant", "content": f" Error: {e}"}
        return {"history": history, "clarifier_state": clarifier_state}, None


with gr.Blocks(
    title=" Business Consultant",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="gray")
) as demo:

    gr.Markdown(
        """
        # Business Consultant
        Let's know why you are here, and i will give you a detailed PDF report  
        """,
    )

    with gr.Row(equal_height=True):
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Conversation",
                height=450,
                type="messages",
                show_copy_button=True
            )
            user_input = gr.Textbox(
                label="Enter your question or clarification:",
                placeholder="Ask your research question or respond to clarifier...",
                lines=2,
                autofocus=True
            )
            submit = gr.Button("Confirm", variant="primary")
        with gr.Column(scale=1):
            file_output = gr.File(
                label="Your report",
                file_count="single",
                height=200
            )

    state = gr.State({"history": [], "clarifier_state": None})

    submit.click(
        fn=run_pipeline_async,
        inputs=[user_input, state],
        outputs=[state, file_output],
    ).then(
        fn=lambda s: (s["history"], ""), 
        outputs=[chatbot, user_input],  
    )

    
    gr.Markdown(
        f"""
        ---
        © {datetime.now().year} — *Automated Multi-Agent Analysis Pipeline*  
        """
    )


if __name__ == "__main__":
    demo.launch()
