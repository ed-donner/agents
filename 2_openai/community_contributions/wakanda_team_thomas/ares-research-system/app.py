"""Quick Gradio app to test the Tavily search tool."""

import gradio as gr
from dotenv import load_dotenv
from ares_tools.search import get_travily_client
load_dotenv()


def run_search(query: str, max_results: int) -> str:
    """Run a Tavily search and return formatted results."""
    if not query.strip():
        return "Please enter a search query."

    client = get_travily_client()
    response = client.search(
        query=query,
        max_results=int(max_results),
        include_answer=True,
    )

    parts: list[str] = []

    if response.get("answer"):
        parts.append(f"## AI Summary\n{response['answer']}\n")

    for i, result in enumerate(response.get("results", []), 1):
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        content = result.get("content", "")
        parts.append(f"### [{i}] {title}\n**URL:** {url}\n\n{content}\n")

    return "\n".join(parts) if parts else "No results found."


demo = gr.Interface(
    fn=run_search,
    inputs=[
        gr.Textbox(label="Search Query", placeholder="e.g. solid-state battery breakthroughs 2026"),
        gr.Slider(minimum=1, maximum=10, value=5, step=1, label="Max Results"),
    ],
    outputs=gr.Markdown(label="Search Results"),
    title="ARES — Tavily Search Test",
    description="Test the Tavily web search tool before wiring it into the agent pipeline.",
)

if __name__ == "__main__":
    demo.launch()
