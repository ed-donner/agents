"""Gradio app: clarifying questions first (OpenAI-style), then autonomous deep research with streaming and optional recipient email."""
import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

manager = ResearchManager()


async def get_clarifying_questions(query: str):
    """Phase 1: generate 3 clarifying questions and show them + answer boxes."""
    if not (query or "").strip():
        return "Please enter a research topic first.", "", "", "", gr.update(visible=True)
    try:
        questions = await manager.get_clarifying_questions(query.strip())
        q1, q2, q3 = (questions + [""] * 3)[:3]
        return (
            "**Answer these to focus the research (optional). You can leave blanks and click Run.**",
            q1,
            q2,
            q3,
            gr.update(visible=True),
        )
    except Exception as e:
        return f"Could not generate questions: {e}", "", "", "", gr.update(visible=True)


async def run_research(
    query: str,
    q1: str,
    q2: str,
    q3: str,
    a1: str,
    a2: str,
    a3: str,
    recipient_email: str,
):
    """Phase 2: refine query with answers and optional recipient email; run agentic research and stream status + report."""
    query = (query or "").strip()
    if not query:
        yield "Please enter a research topic."
        return
    questions = [q1, q2, q3]
    answers = [a1, a2, a3]
    refined = manager.refine_query_with_answers(
        query, questions, answers, recipient_email=(recipient_email or "").strip() or None
    )
    async for chunk in manager.run(refined):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky"), title="Deep Research") as ui:
    gr.Markdown("# Deep Research")
    gr.Markdown(
        "Enter a topic, get 3 clarifying questions (optional to answer), and optionally enter an email to receive the report. Then run."
    )

    query_textbox = gr.Textbox(
        label="What would you like to research?",
        placeholder="e.g. Impact of AI on legal practice in the UK",
    )
    get_questions_btn = gr.Button("Get clarifying questions", variant="primary")

    clar_section = gr.Markdown(value="", label="Clarifications")
    q1_box = gr.Textbox(label="Question 1", interactive=False)
    q2_box = gr.Textbox(label="Question 2", interactive=False)
    q3_box = gr.Textbox(label="Question 3", interactive=False)
    a1_box = gr.Textbox(label="Your answer (optional)")
    a2_box = gr.Textbox(label="Your answer (optional)")
    a3_box = gr.Textbox(label="Your answer (optional)")

    recipient_email_box = gr.Textbox(
        label="Recipient email (optional — report will be sent here after research; leave blank to skip email or use default)",
        placeholder="e.g. colleague@example.com",
    )

    run_btn = gr.Button("Run deep research", variant="secondary")
    report = gr.Markdown(label="Report")

    get_questions_btn.click(
        fn=get_clarifying_questions,
        inputs=query_textbox,
        outputs=[clar_section, q1_box, q2_box, q3_box, run_btn],
    )
    run_btn.click(
        fn=run_research,
        inputs=[
            query_textbox,
            q1_box,
            q2_box,
            q3_box,
            a1_box,
            a2_box,
            a3_box,
            recipient_email_box,
        ],
        outputs=report,
    )
    query_textbox.submit(
        fn=get_clarifying_questions,
        inputs=query_textbox,
        outputs=[clar_section, q1_box, q2_box, q3_box, run_btn],
    )

if __name__ == "__main__":
    # share=True creates a public gradio.live link so others can try your app
    ui.launch(inbrowser=True, share=True)
