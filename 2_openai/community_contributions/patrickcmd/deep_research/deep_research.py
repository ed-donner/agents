import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

manager = ResearchManager()


async def get_clarifying_questions(query: str):
    """Phase 1: Generate clarifying questions and show them in the UI."""
    if not query.strip():
        return (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            "", "", "",
            [],
            "",
        )

    questions_result = await manager.run_clarify(query)
    q_texts = [q.question for q in questions_result.questions[:3]]

    while len(q_texts) < 3:
        q_texts.append("(No additional question)")

    return (
        gr.update(value=f"**Q1:** {q_texts[0]}"),
        gr.update(value=f"**Q2:** {q_texts[1]}"),
        gr.update(value=f"**Q3:** {q_texts[2]}"),
        gr.update(visible=True),
        "", "", "",
        q_texts,
        "Clarifying questions generated. Please answer them below, then click **Start Research**.",
    )


async def run_with_answers(query, answer1, answer2, answer3, state_questions):
    """Phase 2: Refine query, research, evaluate, and iterate."""
    questions = state_questions if state_questions else []
    answers = [answer1, answer2, answer3]
    async for chunk in manager.run_research(query, questions, answers):
        if chunk.startswith("**Evaluation"):
            yield gr.update(), gr.update(visible=True), gr.update(value=chunk)
        else:
            yield gr.update(value=chunk), gr.update(), gr.update()


async def run_skip(query):
    """Skip clarification and go straight to research."""
    async for chunk in manager.run_research(query):
        if chunk.startswith("**Evaluation"):
            yield gr.update(), gr.update(visible=True), gr.update(value=chunk)
        else:
            yield gr.update(value=chunk), gr.update(), gr.update()


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")

    state_questions = gr.State([])

    query_textbox = gr.Textbox(label="What topic would you like to research?")
    with gr.Row():
        submit_button = gr.Button("Get Clarifying Questions", variant="primary")
        skip_button = gr.Button("Skip & Research Directly", variant="secondary")

    status = gr.Markdown(label="Status")

    with gr.Column(visible=False) as clarify_section:
        gr.Markdown("### Clarifying Questions")
        gr.Markdown("Answer the questions below to help focus the research:")
        q1_label = gr.Markdown("")
        answer1 = gr.Textbox(label="Your answer to Q1", lines=2)
        q2_label = gr.Markdown("")
        answer2 = gr.Textbox(label="Your answer to Q2", lines=2)
        q3_label = gr.Markdown("")
        answer3 = gr.Textbox(label="Your answer to Q3", lines=2)
        research_button = gr.Button("Start Research", variant="primary")

    with gr.Accordion("Evaluation Details", open=False, visible=False) as eval_section:
        eval_display = gr.Markdown("")

    report = gr.Markdown(label="Report")

    submit_button.click(
        fn=get_clarifying_questions,
        inputs=[query_textbox],
        outputs=[
            q1_label, q2_label, q3_label,
            clarify_section,
            answer1, answer2, answer3,
            state_questions,
            status,
        ],
    )

    research_button.click(
        fn=run_with_answers,
        inputs=[query_textbox, answer1, answer2, answer3, state_questions],
        outputs=[report, eval_section, eval_display],
    )

    skip_button.click(
        fn=run_skip,
        inputs=[query_textbox],
        outputs=[report, eval_section, eval_display],
    )

ui.launch(inbrowser=True)
