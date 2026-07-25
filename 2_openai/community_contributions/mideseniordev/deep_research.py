import gradio as gr
from dotenv import load_dotenv

from research_manager import ResearchManager

load_dotenv(override=True)

manager = ResearchManager()


async def generate_questions(query: str):
    if not query or not query.strip():
        return (
            "Please provide a research topic first.",
            "",
            "",
            "",
            query,
        )

    clarification = await manager.get_clarifying_questions(query.strip())
    questions = clarification.questions
    return (
        "Clarifying questions generated. Answer them, then click Run Upgraded Research.",
        questions[0],
        questions[1],
        questions[2],
        query.strip(),
    )


async def run_upgraded_research(query_state: str, answer_1: str, answer_2: str, answer_3: str):
    query = (query_state or "").strip()
    if not query:
        yield "Please generate clarifying questions first."
        return

    answers = [answer_1 or "", answer_2 or "", answer_3 or ""]
    async for chunk in manager.run(query, answers):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Upgraded Deep Research")
    gr.Markdown(
        "This version adds: **3 clarifying questions**, **search tuning**, "
        "**manager agents-as-tools orchestration**, and **handoffs to writer + reviewer**."
    )

    query_textbox = gr.Textbox(
        label="What topic would you like to research?",
        placeholder="Example: Compare top open-source vector databases for RAG in 2026.",
    )

    with gr.Row():
        generate_button = gr.Button("1) Generate Clarifying Questions", variant="secondary")
        run_button = gr.Button("2) Run Upgraded Research", variant="primary")

    status_box = gr.Markdown("Enter a topic and generate clarifying questions.")

    gr.Markdown("### Clarification Answers (leave blank to use safe defaults)")
    question_1 = gr.Textbox(label="Q1 - Deliverable and citation format")
    answer_1 = gr.Textbox(label="Your answer for Q1")
    question_2 = gr.Textbox(label="Q2 - Allowed tools and providers")
    answer_2 = gr.Textbox(label="Your answer for Q2")
    question_3 = gr.Textbox(label="Q3 - Evaluation and demo expectations")
    answer_3 = gr.Textbox(label="Your answer for Q3")

    report = gr.Markdown(label="Research Output")
    query_state = gr.State("")

    generate_button.click(
        fn=generate_questions,
        inputs=query_textbox,
        outputs=[status_box, question_1, question_2, question_3, query_state],
    )

    run_button.click(
        fn=run_upgraded_research,
        inputs=[query_state, answer_1, answer_2, answer_3],
        outputs=report,
    )

    query_textbox.submit(
        fn=generate_questions,
        inputs=query_textbox,
        outputs=[status_box, question_1, question_2, question_3, query_state],
    )

ui.launch(inbrowser=True)
