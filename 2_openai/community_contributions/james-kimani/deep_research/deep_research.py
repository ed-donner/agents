from pathlib import Path
import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

env_path = Path(__file__).resolve()
for parent in env_path.parents:
    candidate = parent / ".env"
    if candidate.exists():
        load_dotenv(candidate, override=True)
        break


async def run_research(topic: str, run_evaluation: bool):
    try:
        async for update in ResearchManager().stream_research(
            topic or "",
            skip_evaluate=not run_evaluation,
        ):
            yield update
    except Exception as exc:
        yield f"**Error:** {exc}"


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep research")

    topic = gr.Textbox(label="Research topic", placeholder="e.g. Compare battery tech for EVs in 2026", lines=2)
    run_eval = gr.Checkbox(label="Include evaluation (extra API call)", value=False)
    run_btn = gr.Button("Run research", variant="primary")
    report = gr.Markdown(label="Output")

    run_btn.click(fn=run_research, inputs=[topic, run_eval], outputs=report)
    topic.submit(fn=run_research, inputs=[topic, run_eval], outputs=report)

ui.launch(inbrowser=True)
