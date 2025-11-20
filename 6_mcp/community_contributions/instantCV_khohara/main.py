import asyncio
from agentsListF import run_cv_agent, run_extender_agent, run_html_agent, convert_html_to_pdf
from IPython.display import Markdown, display
from agents import Agent, Runner, trace, Tool
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from IPython.display import display, Markdown
from openai import AsyncOpenAI
import pdfkit
import os
import asyncio
import gradio as gr
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")

async def build_cv(name, email, phone, education, experience, skills):
    # Format details
    details = f"""
Name: {name}
Email: {email}
Contact: {phone}
Education: {education}
Experience: {experience}
Skills: {skills}
"""
    # Step 1 → Save info in cv.md
    with trace("CVM"):
        await run_cv_agent(details)

    # Step 2 → Improve CV content
        await run_extender_agent()

    # Step 3 → Convert to styled HTML
        await run_html_agent()

    # Step 4 → Export to PDF
        pdf_file = convert_html_to_pdf(input_file="cv.html", output_file="cv.pdf")

    # Return clickable link
        #return f"[Click here to download your CV PDF]({pdf_file})"
        pdf_path = os.path.abspath("cv.pdf")
        return "Please Click Here to Download Your CV:",pdf_path

# Wrapper for Gradio since it doesn't handle async directly
def build_cv_sync(name, email, phone, education, experience, skills):
   return asyncio.run(build_cv(name, email, phone, education, experience, skills))

with gr.Blocks() as demo:
    gr.Markdown("# 🚀 RapidResume\n**Make your CV in 60 seconds — answer 6 questions and download your PDF!**")

    with gr.Row():
        name = gr.Textbox(label="Full Name")
        email = gr.Textbox(label="Email")
        phone = gr.Textbox(label="Phone")

    with gr.Row():
        education = gr.Textbox(label="Education")
        experience = gr.Textbox(label="Experience")
        skills = gr.Textbox(label="Skills (comma separated)")

    submit = gr.Button("Generate CV")
    msg_output = gr.Markdown()
    file_output = gr.File(label="Your CV PDF")

    submit.click(
        fn=build_cv_sync,
        inputs=[name, email, phone, education, experience, skills],
        outputs=[msg_output,file_output]
    )

if __name__ == "__main__":
    demo.launch()
