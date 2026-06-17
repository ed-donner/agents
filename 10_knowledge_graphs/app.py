"""
Week 10 App — Knowledge Graph Explorer
Paste text → build a graph → ask multi-hop questions.
Run: python app.py
"""

import gradio as gr
from dotenv import load_dotenv
from knowledge_graph import KnowledgeGraph

load_dotenv(override=True)

_kg = KnowledgeGraph()


def build_graph(text: str):
    global _kg
    _kg = KnowledgeGraph()
    triples = _kg.add_text(text)
    stats = _kg.stats()
    triples_display = "\n".join(
        f"({t.subject}) --[{t.predicate}]--> ({t.obj})  [{t.confidence:.0%}]"
        for t in triples
    )
    summary = f"Graph built: {stats['nodes']} entities, {stats['edges']} relationships, {stats['predicates']} unique predicates"
    return triples_display, summary


def ask_question(question: str):
    if not _kg or _kg.stats()["edges"] == 0:
        return "Build a graph first by pasting text above."
    return _kg.answer_question(question)


DEMO_TEXT = """
Elon Musk founded SpaceX in 2002 and Tesla in 2003.
SpaceX is headquartered in Hawthorne, California.
Tesla is headquartered in Austin, Texas.
Gwynne Shotwell is the President of SpaceX and reports to Elon Musk.
Sam Altman is the CEO of OpenAI, which is based in San Francisco.
Microsoft invested in OpenAI. OpenAI developed ChatGPT.
California and Texas are states in the United States.
"""

with gr.Blocks(title="Week 10 — Knowledge Graph") as demo:
    gr.Markdown("# Week 10: Knowledge Graph\nBuild a knowledge graph from text, then ask multi-hop questions.")

    with gr.Row():
        text_input = gr.Textbox(label="Paste text to build graph from", value=DEMO_TEXT, lines=10)
        build_btn = gr.Button("Build Graph", variant="primary")

    triples_out = gr.Textbox(label="Extracted triples", lines=15)
    stats_out = gr.Textbox(label="Graph stats")

    gr.Markdown("---")
    question_input = gr.Textbox(
        label="Ask a question (try multi-hop: 'What country is the president of SpaceX's employer in?')",
        placeholder="What country is SpaceX headquartered in?",
    )
    ask_btn = gr.Button("Ask")
    answer_out = gr.Textbox(label="Answer", lines=5)

    build_btn.click(build_graph, inputs=[text_input], outputs=[triples_out, stats_out])
    ask_btn.click(ask_question, inputs=[question_input], outputs=[answer_out])

if __name__ == "__main__":
    demo.launch()
