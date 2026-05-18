"""Gradio UI for LangGraph job agency (CV -> browser search -> evaluate -> save + Pushover)."""

import asyncio
import uuid

import gradio as gr
from dotenv import load_dotenv
from graph import DEFAULT_MAX_SEARCH_ATTEMPTS, JobAgencyGraph
from langgraph.checkpoint.memory import MemorySaver

load_dotenv(override=True)


class JobAgencyRunner:
    """One compiled graph + checkpointer per UI session."""

    def __init__(self, agency: JobAgencyGraph) -> None:
        self.thread_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.agency = agency
        self.graph = agency.build(checkpointer=self.memory)

    @classmethod
    async def create(cls) -> "JobAgencyRunner":
        agency = await JobAgencyGraph.create()
        return cls(agency)

    async def cleanup(self) -> None:
        await self.agency.cleanup()


async def setup() -> JobAgencyRunner:
    return await JobAgencyRunner.create()


async def find_matching_jobs(runner: JobAgencyRunner, cv: str) -> str:
    text = (cv or "").strip()
    if not text:
        return "## Error\n\nPlease paste your CV."

    config = {"configurable": {"thread_id": runner.thread_id}}
    initial = {
        "cv": text,
        "search_attempt_count": 0,
        "max_search_attempts": DEFAULT_MAX_SEARCH_ATTEMPTS,
        "candidate_jobs": [],
        "approved_jobs": [],
        "rejected_jobs": [],
        "search_hints": "",
    }
    try:
        result = await runner.graph.ainvoke(initial, config=config)
    except Exception as exc:  # noqa: BLE001
        return f"## Error\n\n{type(exc).__name__}: {exc}"

    md = result.get("final_markdown") or ""
    paths = []
    if result.get("output_md_path"):
        paths.append(f"- Markdown: `{result['output_md_path']}`")
    if result.get("output_json_path"):
        paths.append(f"- JSON: `{result['output_json_path']}`")
    notify = result.get("notify_status", "")
    extra = ""
    if paths:
        extra = "\n\n**Saved files**\n" + "\n".join(paths)
    if notify:
        extra += f"\n\n**Notification:** `{notify}`"
    return md + extra


async def reset(runner: JobAgencyRunner | None) -> tuple[JobAgencyRunner, str]:
    if runner is not None:
        await runner.cleanup()
    return await JobAgencyRunner.create(), ""


def free_resources(_runner: JobAgencyRunner | None) -> None:
    if _runner is None:
        return
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_runner.cleanup())
    except RuntimeError:
        asyncio.run(_runner.cleanup())


def start() -> None:
    with gr.Blocks(title="Inginia's Job Agency", theme=gr.themes.Default()) as ui:
        gr.Markdown("# Inginia's Job Agency")
        runner = gr.State(delete_callback=free_resources)

        with gr.Row():
            cv = gr.Textbox(label="CV", lines=20)
            review = gr.Markdown(label="Matching Jobs", height=400)
        with gr.Row():
            go = gr.Button(variant="primary", value="Find Matching Jobs")
            reset_btn = gr.Button(variant="stop", value="Reset session")

        ui.load(setup, [], [runner])
        go.click(find_matching_jobs, inputs=[runner, cv], outputs=[review])
        reset_btn.click(reset, [runner], [runner, review])

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    start()
