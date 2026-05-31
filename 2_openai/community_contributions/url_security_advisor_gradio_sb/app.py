import gradio as gr
from dotenv import load_dotenv
from general_manager import GeneralManager

load_dotenv(override=True)


stages = [
        "Planning checks...",
        "Running security checks...",
        "Generating report...",
        "Sending email...",
        "Completed ✅"
    ]
total = len(stages)

gm = GeneralManager()

async def run(url: str, email:str):
    email = email or None  
    progress = 0
    async for part in gm.run(url, email):
        progress = min(progress + (100 / total), 100)
        yield part, gr.update(value=progress)

with gr.Blocks(theme=gr.themes.Soft(),  css="""
    #security_report {
        background-color: var(--block-background-fill); /* same as textbox gray */
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 8px;
        min-height: 220px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) inset;
        overflow-y: auto;
    }
    """) as demo:
    with gr.Row():
        with gr.Column(scale=1):
            image = gr.Image(
                "https_advisor.png",
                height=100,
                width=100, 
                show_label=False,
                interactive=False,
            )
        with gr.Column(scale=11):
            gr.Markdown("# 🔒 URL Security Advisor")
            gr.Markdown("## Get a detailed audit of your url security configuration")
            gr.Markdown("<div style='color:#6366f1;'>Sending email might fail if emails are bounced back or when free trial is finished :)</div>")
    with gr.Row():
        with gr.Column():
            url = gr.Textbox(label="Url to be checked out")
    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            button = gr.Button("Run Security Report")
        with gr.Column(scale=1):
            email = gr.Textbox(label="Email to send the report to")
            progress_bar = gr.Slider(0, 100, value=0, interactive=False, label="Progress (%)")
    gr.Markdown("<br>") 
    with gr.Row():
        with gr.Column():
            gr.Markdown("<br>")  
            security_report = gr.Markdown(label="Security Report")
    button.click(fn=run, inputs=[url, email], outputs=[security_report, progress_bar])
demo.launch()