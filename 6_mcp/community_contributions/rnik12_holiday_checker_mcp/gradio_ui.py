import gradio as gr
import asyncio
from agent import run_holiday_agent


def build_ui():
    with gr.Blocks(title="Holiday Checker (MCP)", fill_width=True) as ui:
        gr.Markdown("## 🗓️ Holiday Checker — MCP Server + Agents SDK + Gradio")

        with gr.Tab("Chat"):
            chat = gr.Chatbot(type="messages", label="Ask about holidays", height=460)
            with gr.Row():
                msg = gr.Textbox(placeholder="e.g., Are there holidays in India between 2025-12-20 and 2026-01-05?")
            with gr.Row():
                send = gr.Button("Send", variant="primary")
                clear = gr.Button("Clear")
            state = gr.State([])

            async def respond(message, history):
                if not message or not message.strip():
                    return "", history
                history = list(history or [])
                history.append({"role": "user", "content": message})
                try:
                    reply = await run_holiday_agent(message)
                except Exception as e:
                    reply = f"Agent error: {e}"
                history.append({"role": "assistant", "content": str(reply)})
                return "", history

            msg.submit(respond, [msg, state], [msg, chat])
            send.click(respond, [msg, state], [msg, chat])
            clear.click(lambda: ([], ""), outputs=[chat, msg])

        with gr.Tab("Form"):
            gr.Markdown("### Check a range quickly")
            country = gr.Textbox(label="Country (code or name)", value="IN")
            state = gr.Textbox(label="State/Province (optional)", placeholder="e.g., CA or California")
            city = gr.Textbox(label="City (optional)", placeholder="Display only")
            start = gr.Textbox(label="Start date (YYYY-MM-DD)", value="2025-12-20")
            end = gr.Textbox(label="End date (YYYY-MM-DD)", value="2026-01-05")
            run_btn = gr.Button("Check Holidays", variant="primary")
            out = gr.Markdown()

            async def run_form(cntry, st, ct, s, e):
                q = (
                    f"Check holidays in {cntry}"
                    + (f" state {st}" if st else "")
                    + (f", city {ct}" if ct else "")
                    + f" between {s} and {e}. "
                    "Return a short summary and a bullet list."
                )
                try:
                    resp = await run_holiday_agent(q)
                except Exception as ex:
                    resp = f"Agent error: {ex}"
                return str(resp)

            run_btn.click(run_form, [country, state, city, start, end], [out])

    return ui


if __name__ == "__main__":
    app = build_ui()
    # same ports convention as other contributions
    app.launch(server_name="0.0.0.0", server_port=7862, share=False)
