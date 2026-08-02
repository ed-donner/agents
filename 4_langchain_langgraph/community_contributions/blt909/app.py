import os
import queue
import threading
import asyncio
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import gradio as gr
from PIL import Image, ImageDraw

from pipeline import run_pipeline, PipelineState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# STARTUP — Directories & Assets
# ---------------------------------------------------------------------------

ASSETS_DIR = Path(__file__).parent / "assets"
OUTPUT_DIR = Path(__file__).parent / "output"

ASSETS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

EXECUTOR = ThreadPoolExecutor(max_workers=4)


def create_placeholder_avatar(
    path: Path, fill_color: str, text_color: str = "white", letter: str = "?"
):
    """
    Generate a simple circular avatar PNG using Pillow.
    Uses img.save() (not tobytes()) so the file is a valid PNG.
    """
    if path.exists():
        return
    size = 80
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=fill_color)
    # Draw a simple letter in the center
    try:
        draw.text((size // 2, size // 2), letter, fill=text_color, anchor="mm")
    except Exception:
        pass  # anchor param may not be supported on all Pillow versions
    img.save(str(path), format="PNG")


create_placeholder_avatar(ASSETS_DIR / "user.png", fill_color="#4f46e5", letter="U")
create_placeholder_avatar(ASSETS_DIR / "bot.png", fill_color="#7c3aed", letter="AI")


# ---------------------------------------------------------------------------
# PIPELINE BRIDGE — Thread + Queue pattern
# ---------------------------------------------------------------------------


def run_pipeline_threaded(
    user_prompt: str,
    user_feedback: str | None,
    max_iterations: int,
    output_dir: str,
    msg_queue: queue.Queue,
):
    """
    Run the async pipeline in a dedicated thread with its own event loop.
    Posts STATUS messages and a final __DONE__ / ERROR sentinel to msg_queue.
    """

    def on_status(message: str):
        msg_queue.put(("STATUS", message))

    async def _run():
        return await run_pipeline(
            user_prompt=user_prompt,
            user_feedback=user_feedback,
            max_iterations=max_iterations,
            on_status=on_status,
            output_dir=output_dir,
        )

    try:
        result = asyncio.run(_run())
        msg_queue.put(("__DONE__", result))
    except Exception as e:
        logger.error(f"Pipeline thread error: {e}", exc_info=True)
        msg_queue.put(("ERROR", str(e)))


# ---------------------------------------------------------------------------
# GRADIO UI
# ---------------------------------------------------------------------------


def build_ui() -> gr.Blocks:
    """Build and return the Gradio Blocks application."""

    with gr.Blocks(title="🏠 AI Homepage Generator") as app:
        # Apply theme and CSS via launch() instead of constructor
        pass  # Will be applied in launch()

        gr.Markdown(
            "# 🏠 AI Homepage Generator\n"
            "Describe your dream homepage — our multi-agent AI (GPT-5 · Gemini 2.5 Pro · Claude Sonnet) will build and validate it for you."
        )

        with gr.Row():
            # ── Left Column: Chat ──────────────────────────────────────────
            with gr.Column(scale=7):
                chatbot = gr.Chatbot(
                    value=[],
                    height=600,
                    avatar_images=(
                        str(ASSETS_DIR / "user.png"),
                        str(ASSETS_DIR / "bot.png"),
                    ),
                    render=False,
                    show_label=False,
                    container=True,
                    type='messages',
                )

                with gr.Row():
                    user_input = gr.Textbox(
                        lines=2,
                        placeholder="Describe the homepage you want to build...",
                        label=None,
                        autofocus=True,
                        scale=5,
                        container=False,
                    )
                    submit_btn = gr.Button(
                        "✦ Generate",
                        variant="primary",
                        scale=1,
                        min_width=120,
                    )

                new_project_btn = gr.Button(
                    "✦ New project",
                    variant="secondary",
                    visible=False,
                    size="sm",
                )

            # ── Right Column: Status Panel ────────────────────────────────
            with gr.Column(scale=3, elem_classes=["status-panel"]):
                gr.Markdown("## Pipeline Status")
                status_text = gr.Markdown("*Ready — enter your prompt to begin.*")

                guidelines_json = gr.JSON(
                    label="Current Guidelines",
                    visible=False,
                )
                validation_report_md = gr.Markdown(
                    value="",
                    elem_id="validation-report",
                    visible=False,
                )

        # ── Session State ──────────────────────────────────────────────────
        pipeline_state = gr.State(
            {
                "user_prompt": "",
                "user_feedback": None,
                "iteration": 0,
                "run_count": 0,
            }
        )
        ui_mode = gr.State("initial")  # "initial" | "feedback"
        run_count = gr.State(0)

        # ── Event Handlers ─────────────────────────────────────────────────

        def submit_handler(
            user_text: str,
            chat_history: list,
            p_state: dict,
            mode: str,
            r_count: int,
        ):
            """
            Main event handler: spawns the pipeline thread and streams
            status messages into the chatbot as they arrive.
            Yields tuples matching the outputs list on every update.
            """
            if not user_text.strip():
                # Nothing to do — yield current state unchanged
                yield (
                    chat_history,
                    p_state,
                    mode,
                    r_count,
                    gr.update(),  # submit_btn
                    gr.update(),  # status_text
                    gr.update(),  # guidelines_json
                    gr.update(),  # validation_report_md
                    gr.update(),  # new_project_btn
                    "",  # clear user_input
                )
                return

            # 1. Append user message to chat
            chat_history = chat_history + [{"role": "user", "content": user_text}]

            # 2. Build pipeline args depending on mode
            if mode == "initial":
                prompt = user_text
                feedback = None
                new_p_state = {
                    "user_prompt": user_text,
                    "user_feedback": None,
                    "iteration": 0,
                    "run_count": r_count + 1,
                }
            else:
                prompt = p_state["user_prompt"]
                feedback = user_text
                new_p_state = {
                    "user_prompt": p_state["user_prompt"],
                    "user_feedback": user_text,
                    "iteration": 0,
                    "run_count": r_count + 1,
                }

            new_r_count = r_count + 1

            # 3. Disable button, show running state
            yield (
                chat_history,
                new_p_state,
                mode,
                new_r_count,
                gr.update(value="⏳ Running...", interactive=False),
                gr.update(value="🔄 Pipeline running..."),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                "",  # clear input
            )

            # 4. Launch pipeline thread
            msg_queue: queue.Queue = queue.Queue()
            thread = threading.Thread(
                target=run_pipeline_threaded,
                args=(prompt, feedback, 3, str(OUTPUT_DIR), msg_queue),
                daemon=True,
            )
            thread.start()

            guidelines_shown = False

            # 5. Stream messages from queue
            while True:
                try:
                    item = msg_queue.get(timeout=120)
                except queue.Empty:
                    chat_history = chat_history + [
                        {"role": "assistant", "content": "⚠️ **Timeout** — The pipeline took too long to respond."}
                    ]
                    yield (
                        chat_history,
                        new_p_state,
                        mode,
                        new_r_count,
                        gr.update(
                            value="✦ Generate" if mode == "initial" else "✦ Improve",
                            interactive=True,
                        ),
                        gr.update(value="⚠️ Timeout"),
                        gr.update(),
                        gr.update(),
                        gr.update(),
                        "",
                    )
                    break

                if item[0] == "ERROR":
                    error_msg = f"❌ **Pipeline error:** {item[1]}"
                    chat_history = chat_history + [{"role": "assistant", "content": error_msg}]
                    yield (
                        chat_history,
                        new_p_state,
                        "feedback",
                        new_r_count,
                        gr.update(value="✦ Improve", interactive=True),
                        gr.update(value="❌ Error"),
                        gr.update(),
                        gr.update(),
                        gr.update(visible=True),
                        "",
                    )
                    break

                if item[0] == "STATUS":
                    status_msg = item[1]
                    chat_history = chat_history + [{"role": "assistant", "content": status_msg}]

                    # Show guidelines panel once planner posts its summary
                    show_guidelines = (
                        guidelines_shown is False and "Brief ready" in status_msg
                    )
                    if show_guidelines:
                        guidelines_shown = True

                    # Show validation panel once validator posts
                    show_validation = (
                        "Approved" in status_msg or "Issues found" in status_msg
                    )

                    # Determine right-panel updates
                    guidelines_update = (
                        gr.update(visible=True) if show_guidelines else gr.update()
                    )
                    validation_update = (
                        gr.update(visible=True) if show_validation else gr.update()
                    )

                    yield (
                        chat_history,
                        new_p_state,
                        mode,
                        new_r_count,
                        gr.update(value="⏳ Running...", interactive=False),
                        gr.update(value="🔄 " + status_msg.split("\n")[0][:80]),
                        guidelines_update,
                        validation_update,
                        gr.update(visible=False),
                        "",
                    )

                if item[0] == "__DONE__":
                    final_state: PipelineState = item[1]
                    final_status = final_state.get("status", "error")
                    validation_report = final_state.get("validation_report")

                    if final_status == "done":
                        report = validation_report
                        scores_md = ""
                        if report:
                            s = report.scores
                            scores_md = (
                                f"\n\n| Dimension | Score |\n|---|---|\n"
                                f"| HTML Quality | {s.html_quality * 10:.1f}/10 |\n"
                                f"| Guideline Match | {s.guideline_conformance * 10:.1f}/10 |\n"
                                f"| Visual Render | {s.visual_render * 10:.1f}/10 |\n"
                                f"| **Overall** | **{s.overall * 10:.1f}/10** |\n"
                            )

                        final_msg = (
                            f"🏁 **Pipeline Complete** ✅  *(run #{new_r_count})*\n\n"
                            f"Homepage ready after {final_state.get('iteration', 1)} iteration(s)."
                            f"{scores_md}\n"
                            f"📄 `{OUTPUT_DIR / 'homepage.html'}`\n"
                            f"📸 `{OUTPUT_DIR / 'screenshot.png'}`\n"
                            f"📸 `{OUTPUT_DIR / 'screenshot_mobile.png'}`\n\n"
                            f"---\n**What would you like to improve?** Type below."
                        )
                        chat_history = chat_history + [{"role": "assistant", "content": final_msg}]

                        # Build validation report for right panel
                        report_md = ""
                        if validation_report:
                            s = validation_report.scores
                            report_md = (
                                f"### ✅ Validation Passed\n\n"
                                f"| Dimension | Score |\n|---|---|\n"
                                f"| HTML Quality | {s.html_quality * 10:.1f}/10 |\n"
                                f"| Guideline Match | {s.guideline_conformance * 10:.1f}/10 |\n"
                                f"| Visual Render | {s.visual_render * 10:.1f}/10 |\n"
                                f"| **Overall** | **{s.overall * 10:.1f}/10** |\n"
                            )

                        yield (
                            chat_history,
                            new_p_state,
                            "feedback",
                            new_r_count,
                            gr.update(value="✦ Improve", interactive=True),
                            gr.update(value="✅ Done"),
                            gr.update(visible=guidelines_shown),
                            gr.update(value=report_md, visible=bool(report_md)),
                            gr.update(visible=True),  # show new_project_btn
                            "",
                        )

                    else:
                        # Pipeline ended with error or exhausted iterations
                        errors = final_state.get("errors", ["Unknown error"])
                        report = final_state.get("validation_report")
                        score_str = (
                            f"{report.scores.overall * 10:.1f}/10" if report else "N/A"
                        )

                        issues_str = ""
                        if report and report.issues:
                            critical = [
                                i for i in report.issues if i.severity == "critical"
                            ]
                            issues_str = "\n".join(
                                f"  • {i.description}" for i in critical[:3]
                            )

                        final_msg = (
                            f"🏁 **Pipeline Failed** ❌\n\n"
                            f"Could not produce a passing homepage after {final_state.get('iteration', 3)} iteration(s).\n"
                            f"**Last score:** {score_str}\n"
                        )
                        if issues_str:
                            final_msg += f"**Remaining issues:**\n{issues_str}\n\n"
                        final_msg += "Try rephrasing your prompt or provide specific guidance below."

                        chat_history = chat_history + [{"role": "assistant", "content": final_msg}]

                        yield (
                            chat_history,
                            new_p_state,
                            "feedback",
                            new_r_count,
                            gr.update(value="✦ Improve", interactive=True),
                            gr.update(value="❌ Failed"),
                            gr.update(),
                            gr.update(visible=False),
                            gr.update(visible=True),
                            "",
                        )

                    break

        def new_project_handler():
            """Reset all session state for a fresh project."""
            return (
                [],  # chatbot
                {
                    "user_prompt": "",
                    "user_feedback": None,
                    "iteration": 0,
                    "run_count": 0,
                },  # pipeline_state
                "initial",  # ui_mode
                0,  # run_count
                gr.update(value="✦ Generate", interactive=True),  # submit_btn
                gr.update(value="*Ready — enter your prompt to begin.*"),  # status_text
                gr.update(visible=False),  # guidelines_json
                gr.update(value="", visible=False),  # validation_report_md
                gr.update(visible=False),  # new_project_btn
            )

        # ── Wire up events ─────────────────────────────────────────────────

        handler_outputs = [
            chatbot,
            pipeline_state,
            ui_mode,
            run_count,
            submit_btn,
            status_text,
            guidelines_json,
            validation_report_md,
            new_project_btn,
            user_input,  # cleared after submit
        ]

        submit_btn.click(
            fn=submit_handler,
            inputs=[user_input, chatbot, pipeline_state, ui_mode, run_count],
            outputs=handler_outputs,
        )

        user_input.submit(
            fn=submit_handler,
            inputs=[user_input, chatbot, pipeline_state, ui_mode, run_count],
            outputs=handler_outputs,
        )

        new_project_btn.click(
            fn=new_project_handler,
            inputs=[],
            outputs=[
                chatbot,
                pipeline_state,
                ui_mode,
                run_count,
                submit_btn,
                status_text,
                guidelines_json,
                validation_report_md,
                new_project_btn,
            ],
        )

    return app


# ---------------------------------------------------------------------------
# LAUNCH
# ---------------------------------------------------------------------------


def main():
    """Entry point."""
    from dotenv import load_dotenv

    load_dotenv()

    # Validate API keys early
    missing = []
    for key in ["OPENAI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"]:
        if not os.getenv(key):
            missing.append(key)
    if missing:
        logger.warning(
            f"Missing API keys: {', '.join(missing)} — some agents may fail."
        )

    app = build_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()