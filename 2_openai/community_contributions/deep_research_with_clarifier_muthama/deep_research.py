import gradio as gr
from dotenv import load_dotenv

from research_manager import ResearchManager


load_dotenv(override=True)


async def get_clarifying_questions_ui(query: str):
    try:
        formatted, clarifying_questions = await ResearchManager().get_clarifying_questions(query)
    except ValueError as e:
        return ("Please provide a more specific query (5–100 characters).", [], gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
    return (formatted, clarifying_questions, gr.update(visible=True), gr.update(visible=True), gr.update(visible=True))


async def submit_answer(answer, answers_list, questions_list, current_index, original_query):
    if not answer or len(answer.strip()) > 100:
        return gr.update(value="Answer must be 1-100 characters."), answers_list, current_index, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), ""

    answers_list.append(answer.strip())
    print("Answer submitted:", answer.strip())

    next_index = current_index + 1
    if next_index < len(questions_list):
        next_question = questions_list[next_index].clarifying_question
        formatted = f"**Q{next_index + 1}**: {next_question}"
        return "", answers_list, next_index, gr.update(value=formatted), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), ""
    else:
        contextualized_query = await ResearchManager.run_contextualizer(original_query, questions_list, answers_list)
        return gr.update(visible=False), answers_list, current_index, gr.update(value=f"**Contextualized Query:** {contextualized_query}"), gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), contextualized_query


async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk


with gr.Blocks(
    theme=gr.themes.Default(primary_hue="sky"), 
    css="""
        .header {margin-bottom: 12px;}
        .controls {gap: 8px;}
        .sidebar {background: #f8fafc; padding: 12px; border-radius: 8px;}
        .report-area {max-height: 70vh; overflow:auto; padding:10px;}
    """
) as ui:
    HEADER_MD = """
        # Deep Research
        Enter a topic, refine it through clarifying questions, then run a multi-step research pipeline that searches,
        synthesizes, writes a long Markdown report, and optionally emails it.
    """

    gr.Markdown(HEADER_MD)

    with gr.Group():
        with gr.Row():
            query_textbox = gr.Textbox(
                label="What topic would you like to research? (5–100 characters)",
                placeholder="e.g., Market sizing for mobile money in Kenya",
                max_lines=1,
            )
        with gr.Row():
            run_button = gr.Button("Submit Research Question", variant="primary")

    with gr.Accordion("Clarifying Questions", open=True) as clarifier_section:
        question_display = gr.Markdown(visible=False)
        answer_box = gr.Textbox(label="Your Answer (1–100 chars)", max_lines=1, visible=False)
        submit_button = gr.Button("Submit Answer", visible=False)
        research_button = gr.Button("Start Research", visible=False, variant="secondary")

    with gr.Group():
        research_report = gr.Markdown(label="Research Report", visible=False)
        download_button = gr.Button("Download Report", visible=False)

    questions_state = gr.State([])
    answers_state = gr.State([])    
    question_index = gr.State(0)      
    contextualized_query_state = gr.State("")  

    run_button.click(
        fn=get_clarifying_questions_ui,
        inputs=query_textbox,
        outputs=[question_display, questions_state, question_display, answer_box, submit_button]
    )

    submit_button.click(
        fn=submit_answer,
        inputs=[answer_box, answers_state, questions_state, question_index, query_textbox],
        outputs=[answer_box, answers_state, question_index, question_display, submit_button, research_button, research_report, contextualized_query_state]
    )

    research_button.click(
        fn=run,
        inputs=contextualized_query_state,
        outputs=research_report
    )

ui.launch(inbrowser=True)
