import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk

async def get_question(query: str, history: list):

    clarifying_output = await ResearchManager().get_question(query, history)

    return clarifying_output.question, query

async def answer_followup(query: str,current_question:str, answer: str, history:list, n_followup_questions = 3):
    history.append({"question": current_question, "answer":answer})
    if len(history)< n_followup_questions:
        clarifying_output = await ResearchManager().get_question(query,history)
        yield clarifying_output.question , history, ""

    elif len(history) == n_followup_questions :
        print("Researching ..")
        refined_query = await ResearchManager().get_refined_query(query,history)
        async for chunk in run(refined_query):
            yield "Researching..", history, chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")

    run_button = gr.Button("Submit", variant="primary")
    question_textbox = gr.Textbox(interactive=False)

    answer_textbox = gr.Textbox(interactive = True)
    answer_button = gr.Button("Answer", variant="primary")

    query_state = gr.State()
    history_state = gr.State(value=[])
    

    
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=get_question, inputs=[query_textbox, history_state], outputs=[question_textbox, query_state])
    answer_button.click(fn=answer_followup, inputs=[query_state, question_textbox, answer_textbox, history_state], outputs=[question_textbox, history_state, report])

    query_textbox.submit(fn=run, inputs=query_textbox, outputs=[question_textbox, report])

ui.launch(inbrowser=True)

