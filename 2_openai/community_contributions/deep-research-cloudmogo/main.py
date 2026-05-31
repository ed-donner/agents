from dotenv import load_dotenv 
import gradio as gr
from dragents.research_manager import ResearchManager
from dragents.research_ui import (
    apply_answers_to_app_state,
    build_app_state_from_clarification,
    empty_app_state,
    render_question_screen,
    show_output_update,
)
from models.models import AppState, Clarification

load_dotenv(override = True)
MAX_QUESTIONS = 3

# -----------------------------
# Step 1: Get clarification
# -----------------------------
async def get_question_updates(query: str):
    """Fetch clarification questions and directly return UI updates."""
    if not query or not query.strip():
        return render_question_screen(empty_app_state(), MAX_QUESTIONS)
    
    clarification = empty_app_state().ui.clarification
    async for chunk in ResearchManager().run(query):
        if isinstance(chunk, Clarification):
            clarification = chunk
            break

    return render_question_screen(
        build_app_state_from_clarification(query, clarification),
        MAX_QUESTIONS,
    )


# -----------------------------
# Step 2: Run research (streaming)
# -----------------------------
async def run_research(app_state: AppState, a1: str, a2: str, a3: str):
    """Run research and stream results."""
    app_state = apply_answers_to_app_state(app_state, [a1, a2, a3])
    clarification = app_state.ui.clarification

    async for chunk in ResearchManager().run(app_state.query, clarification):
        if isinstance(chunk, str):
            yield chunk

def show_output(app_state: AppState):
    """Reveal the output area right before streaming research results."""
    return show_output_update(app_state)

# -----------------------------
# UI
# -----------------------------
def main():
    print("Hello from deep-research-ai-agent2!")

    with gr.Blocks() as ui:
        gr.Markdown("# 🔍 Deep Research Agent")
        query = gr.Textbox(
            label="What topic would you like to research?",
            placeholder="Enter your research topic and press Enter",
        )

        # Hidden clarification inputs
        with gr.Column():
            q1 = gr.Textbox(visible=False, lines=1, interactive=True)
            q2 = gr.Textbox(visible=False, lines=1, interactive=True)
            q3 = gr.Textbox(visible=False, lines=1, interactive=True)

        app_state = gr.State(empty_app_state())
        submit_btn = gr.Button("Submit Answers", visible=False)
        output = gr.Markdown(visible=False)


               
        # -----------------------------
        # Step 1: Get clarification
        # -----------------------------
        query.submit(
            fn=get_question_updates,
            inputs=query,
            outputs=[q1, q2, q3, submit_btn, app_state],
            show_progress="minimal",
        )

       
        # -----------------------------
        # Step 2: Capture answers and run research
        # -----------------------------
        submit_btn.click(
            fn=show_output,
            inputs=app_state,
            outputs=[output, app_state],
            queue=False,
        ).then(
            fn=run_research,
            inputs=[app_state, q1, q2, q3],
            outputs=output,
        )

    ui.launch(theme=gr.themes.Default(primary_hue="sky"), inbrowser=True)
    

if __name__ == "__main__":
    main()
