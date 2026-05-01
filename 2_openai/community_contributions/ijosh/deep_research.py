import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)
with open("styles.css") as f:
    css = f.read()

force_light_mode = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.href = url.href;
    }
}
"""

def clarifying_questions(user_query):
    return [
        "What exactly do you want to know?",
        "Any constraints I should consider (e.g date, location, etc.)?",
        "Would you like me to site sources ?",
    ]
    
async def run(query: str, questions: list[str], answers: list[str]):
    enriched_query = f"""
        Original user query: {query} \n
        Clarifying Q&A: 
        1. {questions[0]} \n Answer: {answers[0]}
        2. {questions[1]} \n Answer: {answers[1]}
        3. {questions[2]} \n Answer: {answers[2]}
        """.strip()
    async for chunk in ResearchManager().run(enriched_query):
        yield chunk


async def chat_handler(message, history, state):
    report = ""

    if state["phase"] == "idle":
        state.update({"phase": "clarify","original_query": message,"questions": clarifying_questions(message),"answers": [],"q_index": 0})
        question = state['questions'][0]
        history += [{"role": "user", "content": message},{"role": "assistant", "content": f"**1.** {question}"}]
        yield history, state, "", report
        return

    # collect answers
    state["answers"].append(message)
    history += [{"role": "user", "content": message}]
    state["q_index"] += 1

    # ask next question
    if state["q_index"] < 3:
        question = state["questions"][state["q_index"]]
        history += [{"role": "assistant", "content": f"**{state['q_index']+1}.** {question}"}]
        yield history, state, "", report
        return

    # run agent
    history += [{"role": "assistant", "content": "Report generated below."}]
    async for chunk in run(state["original_query"], state["questions"], state["answers"]):
        report += chunk
        yield history, state, "", report 
    state = {"phase": "idle", "original_query": "", "questions": [], "answers": [], "q_index": 0,}

    return 


with gr.Blocks(title="Deep Research",theme=gr.themes.Soft(primary_hue="teal", secondary_hue="amber",neutral_hue="stone",),
css=css, js=force_light_mode,
) as ui:
    with gr.Column():
        gr.Markdown("""<div class="hero-card"><h1>Deep Research Bot</h1></div>""")
    with gr.Row():
        chatbot = gr.Chatbot(type="messages", height=500)
    with gr.Row():
        msgbox = gr.Textbox(placeholder="Ask your research question...")
    with gr.Row():
        report = gr.Markdown(label="Report")
    state = gr.State({
        "phase": "idle",
        "original_query": "",
        "questions": [],
        "answers": [],
        "q_index": 0,
    })

    msgbox.submit(
        fn=chat_handler, inputs=[msgbox, chatbot, state], 
        outputs=[chatbot, state, msgbox, report], show_progress="full"
    )

ui.launch(inbrowser=True)