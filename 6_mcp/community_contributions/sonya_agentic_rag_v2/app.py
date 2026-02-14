import gradio as gr
from agentic_rag import AgenticRAG
from documents_retrievers import SEMANTIC_RETRIEVAL, HYBRID_RETRIEVAL_RERANK
import time


async def setup():
    agentic_rag = AgenticRAG()
    await agentic_rag.setup()
    return agentic_rag


async def run(agentic_rag, query):
    full_messages = ""
    # To stream text output and append text in a Gradio Markdown component
    # Generator Function: Your function must be a generator (use the yield keyword).
    # Cumulative Output: The value you yield at each step should be the entire content you want to display
    # Make use of Markdown H1, H2.... Bold, Italic 
    async for progress in agentic_rag.run(query):
        full_messages += '\n' + progress
        time.sleep(0.05)
        yield full_messages

async def reset(selected_index = 1):
    new_agentic_rag = AgenticRAG()
    if selected_index == 0:
        await new_agentic_rag.setup(SEMANTIC_RETRIEVAL)
    else:
        await new_agentic_rag.setup(HYBRID_RETRIEVAL_RERANK)    
    # How do those parameters match
    return "", "", new_agentic_rag


def free_resources(agentic_rag):
    print("Cleaning up")
    try:
        if agentic_rag:
            agentic_rag.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Agentic RAG", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## A Medical Q & A Agentic RAG Assistant")
    agentic_rag = gr.State(delete_callback=free_resources)

    # css = ".medium-font textarea {font-size: 12px !important}"
    # with gr.Group():
    with gr.Blocks():
        with gr.Row():
            radio  = gr.Radio(["Semantic Retrieval", "Hybrid Retrieval Plus ReRank"], label="RAG Retrieval Strategy", 
            value="Hybrid Retrieval Plus ReRank", type='index')
        with gr.Row():
            query  = gr.Textbox(show_label=False, placeholder="Your question to your Assistant:")
        with gr.Row():
            report = gr.Markdown(label="Answer", height=700)     
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [agentic_rag])
   
    go_button.click(
        fn=run, inputs=[agentic_rag, query], outputs=[report]
    )
    query.submit(
        fn=run, inputs=[agentic_rag, query], outputs=[report]
    )
    reset_button.click(reset, [], [query, report, agentic_rag])
    radio.input(fn=reset, inputs=radio, outputs=[query, report, agentic_rag])
    ui.queue(default_concurrency_limit=5)

ui.launch(inbrowser=True)
