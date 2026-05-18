import gradio as gr

from config import RECIPIENT_EMAIL
from pipeline import generate_questions, run_outreach


with gr.Blocks(title="Sales Outreach Agent") as demo:
    gr.Markdown("# Sales Outreach Agent (Week 2 Assessment)")

    with gr.Row():
        company = gr.Textbox(label="Company", placeholder="Acme Corp")
        recipient = gr.Textbox(
            label="Recipient Email (optional override)",
            placeholder=RECIPIENT_EMAIL or "you@example.com",
        )

    questions_btn = gr.Button("Generate Clarifying Questions")
    questions_box = gr.Textbox(label="Clarifying Questions", lines=4)

    with gr.Row():
        target_role = gr.Textbox(label="Target Role", value="CEO")
        primary_pain = gr.Textbox(
            label="Primary Pain",
            value="Slow, manual SOC2 evidence collection",
        )
        desired_cta = gr.Textbox(label="Desired CTA", value="15-minute call next week")

    run_btn = gr.Button("Run Outreach + Send")

    text_body = gr.Textbox(label="Winning Email (Text)", lines=8)
    html_body = gr.HTML(label="Winning Email (HTML)")
    summary = gr.Textbox(label="Selection Summary", lines=4)
    followups = gr.Textbox(label="Follow-up Sequence", lines=6)
    send_status = gr.Textbox(label="Send Status")

    questions_btn.click(generate_questions, inputs=[company], outputs=[questions_box])
    run_btn.click(
        run_outreach,
        inputs=[company, target_role, primary_pain, desired_cta, recipient],
        outputs=[text_body, html_body, summary, followups, send_status],
    )
