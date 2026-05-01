import asyncio
import sys
from pathlib import Path

_app_dir = Path(__file__).resolve().parent
if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))

import gradio as gr
from dotenv import load_dotenv

from research_manager import ResearchManager, ResearchError

load_dotenv(override=True)


async def run_research(query: str, send_email: bool, recipient_email: str):
    if not query or not query.strip():
        yield "❌ Please enter a research query."
        return

    manager = ResearchManager(
        send_email_report=send_email,
        recipient_email=(recipient_email or "").strip() or None,
    )
    try:
        async for chunk in manager.run(query):
            yield chunk
    except ResearchError:
        yield "\n\n*Research was interrupted. Check the trace for details.*"
    except Exception as e:
        yield f"\n\n❌ **Unexpected error:** {str(e)}"


def run_research_sync(query: str, send_email: bool, recipient_email: str) -> str:
    async def _collect() -> str:
        parts: list[str] = []
        async for chunk in run_research(query, send_email, recipient_email):
            parts.append(chunk)
        text = "".join(parts)
        return text if text else "No output."

    return asyncio.run(_collect())


async def run_research_streaming(query: str, send_email: bool, recipient_email: str):
    if not query or not query.strip():
        yield "❌ Please enter a research query."
        return

    manager = ResearchManager(
        send_email_report=send_email,
        recipient_email=(recipient_email or "").strip() or None,
    )
    full_output = []
    try:
        async for chunk in manager.run(query):
            full_output.append(chunk)
            yield "".join(full_output)
    except ResearchError as e:
        full_output.append(f"\n\n❌ Research error: {e}")
        yield "".join(full_output)
    except Exception as e:
        full_output.append(f"\n\n❌ Unexpected error: {str(e)}")
        yield "".join(full_output)


with gr.Blocks(
    title="Deep Research by Asket",
    theme=gr.themes.Soft(primary_hue="sky"),
    css="""
    .gradio-container { max-width: 900px !important; }
    """,
) as ui:
    gr.Markdown(
        """
        # 🔍 Deep Research

        Enter a research topic and get a detailed report with:
        - **Planned web searches** (AI-driven)
        - **Parallel search execution**
        - **Synthesized markdown report**
        - **Optional email delivery** (enter your address below)

        *Uses OpenAI Agents SDK • Model params & guardrails configured*
        """
    )
    with gr.Row():
        query_box = gr.Textbox(
            label="Research topic",
            placeholder="e.g. Latest AI Agent frameworks in 2026",
            lines=2,
        )
    with gr.Row():
        send_email_cb = gr.Checkbox(label="Send report by email", value=True)
        run_btn = gr.Button("Run research", variant="primary")
    recipient_box = gr.Textbox(
        label="Your email (inbox for the report)",
        placeholder="you@example.com",
        lines=1,
    )
    report = gr.Markdown(label="Report")

    run_btn.click(
        fn=run_research_streaming,
        inputs=[query_box, send_email_cb, recipient_box],
        outputs=report,
        show_progress=True,
    )
    query_box.submit(
        fn=run_research_streaming,
        inputs=[query_box, send_email_cb, recipient_box],
        outputs=report,
        show_progress=True,
    )

if __name__ == "__main__":
    ui.launch(inbrowser=True)
