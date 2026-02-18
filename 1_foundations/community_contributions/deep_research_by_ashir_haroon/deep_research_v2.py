import gradio as gr
from dotenv import load_dotenv
from research_manager import run_clarifier, run_research

load_dotenv(override=True)


async def generate_questions(query: str):
    if not query.strip():
        gr.Warning("Please enter a research query first.")
        return [gr.update()] * 7

    questions = await run_clarifier(query)

    return (
        gr.update(value=questions[0], visible=True),
        gr.update(visible=True),
        gr.update(value=questions[1], visible=True),
        gr.update(visible=True),
        gr.update(value=questions[2], visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
    )


async def research(query, q1, a1, q2, a2, q3, a3):
    if not all([a1.strip(), a2.strip(), a3.strip()]):
        gr.Warning("Please answer all three clarifying questions.")
        yield ""
        return

    async for chunk in run_research(query, q1, a1, q2, a2, q3, a3):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research v2")
    gr.Markdown(
        "Enhanced research with **clarifying questions**, "
        "**agents-as-tools**, and **handoffs**."
    )

    # Step 1
    gr.Markdown("### Step 1: Enter your research query")
    query_input = gr.Textbox(
        label="Research Query",
        placeholder="What topic would you like to research?",
        lines=2,
    )
    clarify_btn = gr.Button("Generate Clarifying Questions", variant="secondary")

    # Step 2 — hidden until questions are generated
    gr.Markdown("### Step 2: Answer the clarifying questions")
    q1 = gr.Textbox(label="Question 1", interactive=False, visible=False)
    a1 = gr.Textbox(label="Your Answer", visible=False, placeholder="Type your answer...")
    q2 = gr.Textbox(label="Question 2", interactive=False, visible=False)
    a2 = gr.Textbox(label="Your Answer", visible=False, placeholder="Type your answer...")
    q3 = gr.Textbox(label="Question 3", interactive=False, visible=False)
    a3 = gr.Textbox(label="Your Answer", visible=False, placeholder="Type your answer...")
    research_btn = gr.Button("Run Research", variant="primary", visible=False)

    # Step 3
    gr.Markdown("### Step 3: Report")
    report = gr.Markdown()

    clarify_btn.click(
        fn=generate_questions,
        inputs=query_input,
        outputs=[q1, a1, q2, a2, q3, a3, research_btn],
    )

    research_btn.click(
        fn=research,
        inputs=[query_input, q1, a1, q2, a2, q3, a3],
        outputs=report,
    )

ui.launch(inbrowser=True)
