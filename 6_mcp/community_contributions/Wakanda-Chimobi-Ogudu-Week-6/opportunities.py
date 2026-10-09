from __future__ import annotations

import asyncio
import sys

import gradio as gr

from opportunities_core import (
    LOG_POLL_INTERVAL_SECONDS,
    apply_single_opportunity,
    build_opportunity_table_rows,
    load_applications_from_disk,
    opportunities_to_dataframe,
    silence_http_logging,
)
from opportunities_research import apply_attempt_rank, research_opportunities

__all__ = ["launch"]


def build_gradio_ui():
    async def go(name, url, email, focus):
        activity_log: list[str] = []
        try:
            yield gr.update(interactive=False), "Starting...\n", opportunities_to_dataframe([])
            base = (
                "Paid jobs with a clear employer contact; not accelerators, hackathons, or grants. "
                "Research targets listings where an employer email can be found."
            )
            brief = base + (" " + (focus or "").strip() if (focus or "").strip() else "")
            research_task = asyncio.create_task(
                research_opportunities(name, url, brief, activity_log)
            )
            while not research_task.done():
                await asyncio.sleep(LOG_POLL_INTERVAL_SECONDS)
                yield (
                    gr.update(interactive=False),
                    "\n".join(activity_log),
                    opportunities_to_dataframe([]),
                )
            opportunities, _skipped_count = await research_task
            yield (
                gr.update(interactive=False),
                "\n".join(activity_log),
                opportunities_to_dataframe(
                    build_opportunity_table_rows(
                        opportunities, load_applications_from_disk()
                    )
                ),
            )
            if opportunities and (email or "").strip():
                activity_log.append("")
                activity_log.append("=== Email employers (Mailtrap) ===")
                apply_queue = sorted(opportunities, key=apply_attempt_rank)
                total_apply = len(apply_queue)
                for i, opportunity in enumerate(apply_queue, 1):
                    apply_task = asyncio.create_task(
                        apply_single_opportunity(
                            opportunity,
                            name,
                            url,
                            email.strip(),
                            i,
                            total_apply,
                            activity_log,
                            focus=(focus or "").strip(),
                        )
                    )
                    while not apply_task.done():
                        await asyncio.sleep(LOG_POLL_INTERVAL_SECONDS)
                        yield (
                            gr.update(interactive=False),
                            "\n".join(activity_log),
                            opportunities_to_dataframe(
                                build_opportunity_table_rows(
                                    opportunities, load_applications_from_disk()
                                )
                            ),
                        )
                    await apply_task
                    yield (
                        gr.update(interactive=False),
                        "\n".join(activity_log),
                        opportunities_to_dataframe(
                            build_opportunity_table_rows(
                                opportunities, load_applications_from_disk()
                            )
                        ),
                    )
                activity_log.append("  Email pass complete")
            elif not opportunities:
                activity_log.append("")
                activity_log.append("=== Email employers ===")
                activity_log.append(
                    "  - No rows in the table. Check SERPER_API_KEY, broaden Focus, or try again."
                )
            else:
                activity_log.append("")
                activity_log.append("=== Email employers ===")
                activity_log.append(
                    "  - Add your email for the application body and Mailtrap From (unless SMTP_FROM is set). "
                    "Windows: set MAILTRAP_API_KEY + MAILTRAP_INBOX_ID for sandbox HTTP send (see mailtrap_smtp.py docstring), "
                    "or SMTP creds (subprocess). See mailtrap_config_from_env / mailtrap_http_send_configured."
                )
            activity_log.append("")
            activity_log.append("=== Done ===")
            rows = build_opportunity_table_rows(
                opportunities, load_applications_from_disk()
            )
            yield gr.update(interactive=True), "\n".join(activity_log), opportunities_to_dataframe(rows)
        except Exception as exc:
            activity_log.append(str(exc))
            yield gr.update(interactive=True), "\n".join(activity_log), opportunities_to_dataframe([])
            raise gr.Error(str(exc))

    with gr.Blocks(title="Job search - email employers (Mailtrap)") as app:
        name = gr.Textbox(label="Your name")
        url = gr.Textbox(
            label="LinkedIn profile URL",
            placeholder="https://www.linkedin.com/in/...",
        )
        email = gr.Textbox(
            label="Your email",
        )
        focus = gr.Textbox(
            label="Focus (role, skills, location)",
            lines=2,
            placeholder="e.g. remote PHP Laravel backend",
        )
        btn = gr.Button("Find jobs & send emails", variant="primary")
        log = gr.Textbox(label="Activity log", lines=22, max_lines=40)
        tbl = gr.Dataframe(
            label="Jobs",
            headers=["Title", "URL", "Deadline", "Type", "Channel", "Status"],
            datatype=["str", "html", "str", "str", "str", "str"],
            interactive=False,
        )
        btn.click(go, [name, url, email, focus], [btn, log, tbl])
    return app


def launch() -> None:
    silence_http_logging()
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except AttributeError:
            pass
    build_gradio_ui().launch(share=False)


if __name__ == "__main__":
    launch()
