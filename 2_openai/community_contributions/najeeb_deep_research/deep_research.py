import gradio as gr
from dotenv import load_dotenv
import os
from agents import set_default_openai_client, set_default_openai_api, set_tracing_disabled
from openai import AsyncOpenAI
from state import session_state

load_dotenv(override=True)

from research_manager import ResearchManager

set_default_openai_api("chat_completions")
set_tracing_disabled(True)

base_url = "https://openrouter.ai/api/v1"
api_key = os.getenv("OPENAI_API_KEY")

client = AsyncOpenAI(base_url=base_url, api_key=api_key)
set_default_openai_client(client)

async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    
    # Stage 1: Query input
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")

    # Stage 2: Clarifying questions (hidden until Stage 1)
    with gr.Column(visible=False) as clarifying_section:
        gr.Markdown("### A few quick questions before we dive in:")
        q1 = gr.Textbox(interactive=False, label="Question 1")
        a1 = gr.Textbox(label="Your Answer")

        q2 = gr.Textbox(interactive=False, label="Question 2")
        a2 = gr.Textbox(label="Your Answer")

        q3 = gr.Textbox(interactive=False, label="Question 3")
        a3 = gr.Textbox(label="Your Answer")

        submit_btn = gr.Button("Submit & Research", variant="primary")

    report = gr.Markdown(label="Report")

    # Stage 1: Show questions
    def show_questions(query):
        questions = [
            f"What is the primary goal or outcome you are expecting from: '{query}'?",
            "Are there any constraints or preferences? (e.g. format, length, tone)",
            "Any additional context or background that would help?",
        ]
        session_state["query"] = query
        return (
            gr.update(visible=True),  # show clarifying section
            questions[0],
            questions[1],
            questions[2],
        )

    run_button.click(
        fn=show_questions,
        inputs=[query_textbox],
        outputs=[clarifying_section, q1, q2, q3],
    )
    query_textbox.submit(
        fn=show_questions,
        inputs=[query_textbox],
        outputs=[clarifying_section, q1, q2, q3],
    )

    # Stage 2: Store answers and stream research
    async def submit_answers(answer_1, answer_2, answer_3):
        session_state["answers"] = [answer_1, answer_2, answer_3]
        async for chunk in ResearchManager().run(session_state["query"]):
            yield chunk

    submit_btn.click(
        fn=submit_answers,
        inputs=[a1, a2, a3],
        outputs=[report],
    )

ui.launch(inbrowser=True)