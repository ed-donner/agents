"""
Gradio UI for the Learning Path Generator.
Tool testing mode - testing each tool as we build.
"""

import sys
sys.stdout.reconfigure(line_buffering=True)

import gradio as gr
from tools import get_wikipedia_tool, get_search_tool

print("Starting Learning Planner - Tool Testing...")


wiki_tool = get_wikipedia_tool()
search_tool = get_search_tool()


def test_wikipedia(query: str) -> str:
    """Test the Wikipedia tool with a query."""
    if not query.strip():
        return "Please enter a search query."
    result = wiki_tool.invoke(query)
    return result


def test_web_search(query: str) -> str:
    """Test the web search tool with a query."""
    if not query.strip():
        return "Please enter a search query."
    results = search_tool.invoke(query)
    
    output = []
    for r in results:
        output.append(f"**{r.get('title', 'No title')}**")
        output.append(f"URL: {r.get('url', 'N/A')}")
        output.append(f"{r.get('content', 'No content')}")
        output.append("-" * 50)
    
    return "\n\n".join(output) if output else "No results found."


with gr.Blocks(title="Learning Planner - Tool Testing") as ui:
    gr.Markdown("## Tool Testing")
    
    with gr.Tab("Wikipedia"):
        gr.Markdown("Search Wikipedia for topic overviews.")
        with gr.Row():
            wiki_query = gr.Textbox(
                label="Search Query",
                placeholder="e.g., LangGraph, Machine Learning, Kubernetes"
            )
        with gr.Row():
            wiki_btn = gr.Button("Search Wikipedia", variant="primary")
        with gr.Row():
            wiki_result = gr.Textbox(label="Result", lines=15, show_copy_button=True)
        wiki_btn.click(test_wikipedia, inputs=[wiki_query], outputs=[wiki_result])
        wiki_query.submit(test_wikipedia, inputs=[wiki_query], outputs=[wiki_result])
    
    with gr.Tab("Web Search"):
        gr.Markdown("Search the web for current information.")
        with gr.Row():
            search_query = gr.Textbox(
                label="Search Query",
                placeholder="e.g., LangGraph tutorial 2024, Kubernetes roadmap"
            )
        with gr.Row():
            search_btn = gr.Button("Search Web", variant="primary")
        with gr.Row():
            search_result = gr.Textbox(label="Result", lines=15, show_copy_button=True)
        search_btn.click(test_web_search, inputs=[search_query], outputs=[search_result])
        search_query.submit(test_web_search, inputs=[search_query], outputs=[search_result])


if __name__ == "__main__":
    ui.launch()
