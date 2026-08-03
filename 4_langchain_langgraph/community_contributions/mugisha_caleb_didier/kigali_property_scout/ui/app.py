"""Gradio two-column UI — chat on the left, opportunity cards on the right"""

import uuid
import gradio as gr
from langchain_core.messages import AIMessage, HumanMessage
from agent.graph import build_graph

CUSTOM_CSS = """
.gradio-container {
    background-color: #0f172a !important;
}
.main-title {
    color: #f8fafc !important;
    text-align: center;
    margin-bottom: 0 !important;
}
.subtitle {
    color: #94a3b8 !important;
    text-align: center;
    font-size: 16px;
    margin-top: 4px !important;
}
.panel {
    background-color: #1e293b !important;
    border-radius: 12px;
    padding: 16px !important;
}
.opportunity-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    color: #f8fafc;
}
.opportunity-card h3 {
    color: #38bdf8;
    margin: 0 0 12px 0;
    font-size: 18px;
}
.card-field {
    margin: 6px 0;
    font-size: 14px;
    color: #e2e8f0;
}
.card-label {
    color: #94a3b8;
    font-weight: 600;
    margin-right: 6px;
}
.card-highlights {
    list-style: none;
    padding: 0;
    margin: 8px 0;
}
.card-highlights li {
    color: #4ade80;
    font-size: 13px;
    padding: 2px 0;
}
.card-highlights li::before {
    content: "\\2713\\0020";
}
.card-link {
    color: #38bdf8;
    text-decoration: none;
    font-size: 13px;
}
.card-link:hover {
    text-decoration: underline;
}
.placeholder-text {
    color: #64748b;
    text-align: center;
    padding: 40px 20px;
    font-size: 15px;
}
"""

PLACEHOLDER_HTML = '<p class="placeholder-text">Your property matches will appear here once I find opportunities for you.</p>'
NO_RESULTS_HTML = '<p class="placeholder-text">No properties found matching your criteria. Try adjusting your preferences with a new search.</p>'


def render_cards(opportunities: list) -> str:
    """Generate styled HTML cards from opportunity dicts."""
    if not opportunities:
        return NO_RESULTS_HTML

    html = ""
    for opp in opportunities[:4]:
        highlights = opp.get("highlights", [])[:3]
        highlights_html = "".join(f"<li>{h}</li>" for h in highlights) if highlights else ""

        price = opp.get("price_range") or "Not confirmed"
        payment = opp.get("payment_plan") or "Contact developer"
        source = opp.get("source_link", "")
        source_html = f'<a class="card-link" href="{source}" target="_blank">View source</a>' if source else ""

        html += f"""<div class="opportunity-card">
<h3>{opp.get("project_name") or "Property Listing"}</h3>
<p class="card-field"><span class="card-label">Developer:</span>{opp.get("developer_name") or "Unknown"}</p>
<p class="card-field"><span class="card-label">Location:</span>{opp.get("location") or "Kigali"}</p>
<p class="card-field"><span class="card-label">Type:</span>{opp.get("property_types") or "—"}</p>
<p class="card-field"><span class="card-label">Price:</span>{price}</p>
<p class="card-field"><span class="card-label">Payment:</span>{payment}</p>
{"<ul class='card-highlights'>" + highlights_html + "</ul>" if highlights_html else ""}
{source_html}
</div>"""

    return html


def create_app():
    """Build and return the Gradio Blocks app."""
    graph = build_graph()

    def chat(message: str, history: list, thread_id: str):
        if not message.strip():
            return history, PLACEHOLDER_HTML, "", thread_id

        history.append({"role": "user", "content": message})

        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke({"messages": [("user", message)]}, config=config)

        reply = result["messages"][-1].content
        history.append({"role": "assistant", "content": reply})

        opportunities = result.get("opportunities")
        cards = render_cards(opportunities) if opportunities is not None else PLACEHOLDER_HTML

        return history, cards, "", thread_id

    def reset():
        return [], PLACEHOLDER_HTML, "", str(uuid.uuid4())

    def restore_session(thread_id):
        if not thread_id:
            return [], PLACEHOLDER_HTML, str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        state = graph.get_state(config)
        if not state.values:
            return [], PLACEHOLDER_HTML, thread_id
        history = []
        for m in state.values.get("messages", []):
            if isinstance(m, HumanMessage):
                history.append({"role": "user", "content": m.content})
            elif isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
                history.append({"role": "assistant", "content": m.content})
        opportunities = state.values.get("opportunities")
        cards = render_cards(opportunities) if opportunities is not None else PLACEHOLDER_HTML
        return history, cards, thread_id

    with gr.Blocks(
        title="Kigali Property Scout",
        theme=gr.themes.Default(primary_hue="slate"),
        css=CUSTOM_CSS,
    ) as app:
        gr.Markdown("# Kigali Property Scout", elem_classes="main-title")
        gr.Markdown("Find your perfect property in Kigali, Rwanda", elem_classes="subtitle")

        thread_id = gr.BrowserState(default_value=str(uuid.uuid4()), storage_key="kps_thread_id")

        with gr.Row():
            with gr.Column(scale=1, elem_classes="panel"):
                chatbot = gr.Chatbot(height=480, type="messages", label="Chat", show_label=False)
                msg = gr.Textbox(
                    placeholder="Tell me about your ideal property in Kigali...",
                    show_label=False,
                    container=False,
                )
                new_search_btn = gr.Button("New Search", variant="stop", size="sm")

            with gr.Column(scale=1, elem_classes="panel"):
                gr.Markdown("### Property Opportunities", elem_classes="main-title")
                cards_html = gr.HTML(value=PLACEHOLDER_HTML)

        app.load(restore_session, [thread_id], [chatbot, cards_html, thread_id])
        msg.submit(chat, [msg, chatbot, thread_id], [chatbot, cards_html, msg, thread_id])
        new_search_btn.click(reset, [], [chatbot, cards_html, msg, thread_id])

    return app
