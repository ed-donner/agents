import gradio as gr
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(ROOT, "src"))

# from src.homeworker.main import run
from src.homeworker.main import run

def run_homework(grade, to_email, topic):
    return run(grade, to_email, topic)
    # return "Done"

with gr.Blocks() as demo:
    gr.Markdown("# Homework Automation UI")

    grade = gr.Dropdown(
        choices=["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"],
        label="Select A Grade"
    )

    to_email = gr.Textbox(
        label="Recipient Email",
        placeholder="name@example.com"
    )

    topic = gr.Textbox(
        label="Homework Topic",
        placeholder="Origin of the Universe"
    )

    submit_btn = gr.Button("Run Homework Creator Crew")
    output = gr.Textbox(label="Output")
    submit_btn.click(fn=run_homework, inputs=[grade, to_email, topic], outputs=output)

demo.launch()
