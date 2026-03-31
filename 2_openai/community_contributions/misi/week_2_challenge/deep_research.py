import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def get_clarifications(query: str):
    manager = ResearchManager()
    clarification = await manager.get_clarification_questions(query)
    questions = clarification.questions[:3]
    while len(questions) < 3:
        questions.append("")

    return (
        gr.update(visible=True),
        gr.update(value=questions[0], visible=True),
        gr.update(value=questions[1], visible=True),
        gr.update(value=questions[2], visible=True),
        gr.update(value="", visible=True),
        gr.update(value="", visible=True),
        gr.update(value="", visible=True),
        gr.update(visible=True),
        gr.update(value="Answer the clarification questions, then click Run research."),
        questions,
    )


async def run_research(query: str, questions: list[str], answer_1: str, answer_2: str, answer_3: str):
    manager = ResearchManager()
    answers = [answer_1, answer_2, answer_3]
    refined_query = await manager.refine_query(query, questions, answers)

    yield (
        gr.update(value=refined_query),
        f"Refined query:\n\n{refined_query}\n\nStarting research..."
    )

    async for chunk in manager.run(refined_query):
        yield gr.update(value=refined_query), chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    clarification_questions = gr.State([])

    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    clarify_button = gr.Button("Ask clarification questions", variant="secondary")

    with gr.Column(visible=False) as clarification_section:
        question_1 = gr.Textbox(label="Clarification question 1", interactive=False)
        answer_1 = gr.Textbox(label="Your answer 1")
        question_2 = gr.Textbox(label="Clarification question 2", interactive=False)
        answer_2 = gr.Textbox(label="Your answer 2")
        question_3 = gr.Textbox(label="Clarification question 3", interactive=False)
        answer_3 = gr.Textbox(label="Your answer 3")
        run_button = gr.Button("Run research", variant="primary")

    report = gr.Markdown(label="Report")

    clarify_button.click(
        fn=get_clarifications,
        inputs=query_textbox,
        outputs=[
            clarification_section,
            question_1,
            question_2,
            question_3,
            answer_1,
            answer_2,
            answer_3,
            run_button,
            report,
            clarification_questions,
        ],
    )

    query_textbox.submit(
        fn=get_clarifications,
        inputs=query_textbox,
        outputs=[
            clarification_section,
            question_1,
            question_2,
            question_3,
            answer_1,
            answer_2,
            answer_3,
            run_button,
            report,
            clarification_questions,
        ],
    )

    run_button.click(
        fn=run_research,
        inputs=[query_textbox, clarification_questions, answer_1, answer_2, answer_3],
        outputs=[query_textbox, report],
    )

ui.launch(inbrowser=True)
