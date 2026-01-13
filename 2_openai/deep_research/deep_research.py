import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

manager = ResearchManager()

async def generate_questions(query: str):
    """Generate follow-up questions for the user"""
    if not query.strip():
        return [], gr.update(visible=False), "Please enter a research topic first."
    
    questions = await manager.generate_questions(query)
    # Return questions, make Q&A section visible, and show status
    return questions, gr.update(visible=True), f"Please answer the {len(questions)} questions below to help focus the research:"


async def run_research(query: str, questions: list[str], *answers):
    """Run the research with user's answers"""
    answers_list = list(answers)
    async for chunk in manager.run(query, questions, answers_list):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    
    # Step 1: Enter query
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    generate_button = gr.Button("Generate Questions", variant="secondary")
    status = gr.Markdown("")
    
    # Step 2: Answer questions (initially hidden)
    with gr.Column(visible=False) as qa_section:
        gr.Markdown("### Follow-up Questions")
        gr.Markdown("*Please answer these questions to help focus the research:*")
        answer1 = gr.Textbox(label="Question 1", placeholder="Your answer...")
        answer2 = gr.Textbox(label="Question 2", placeholder="Your answer...")
        answer3 = gr.Textbox(label="Question 3", placeholder="Your answer...")
        answer4 = gr.Textbox(label="Question 4", placeholder="Your answer...")
        answer5 = gr.Textbox(label="Question 5", placeholder="Your answer...")
        run_button = gr.Button("Run Research", variant="primary")
    
    # Step 3: Report
    report = gr.Markdown(label="Report")
    
    # State to store questions
    questions_state = gr.State([])
    
    # Update question labels when questions are generated
    async def update_questions_ui(query):
        questions, visibility, status_msg = await generate_questions(query)
        updates = [questions, visibility, status_msg]
        # Update each answer textbox label with the question
        for i in range(5):
            if i < len(questions):
                updates.append(gr.update(label=questions[i], visible=True))
            else:
                updates.append(gr.update(visible=False))
        return updates
    
    generate_button.click(
        fn=update_questions_ui,
        inputs=query_textbox,
        outputs=[questions_state, qa_section, status, answer1, answer2, answer3, answer4, answer5]
    )
    
    run_button.click(
        fn=run_research,
        inputs=[query_textbox, questions_state, answer1, answer2, answer3, answer4, answer5],
        outputs=report
    )

ui.launch(inbrowser=True)

