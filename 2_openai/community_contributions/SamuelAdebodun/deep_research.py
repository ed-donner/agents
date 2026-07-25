"""Week 2 deep research — notebook `week2_deep_research.ipynb` or `python deep_research.py`."""

from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


def _course_env_file(start: Path) -> Path | None:
    for d in (start, *start.parents):
        if (d / "2_openai").is_dir() and (d / ".env").is_file():
            return d / ".env"
    return None


def _load_env() -> None:
    env = _course_env_file(Path(__file__).resolve().parent)
    if env is not None:
        load_dotenv(env, override=True, encoding="utf-8-sig")
    else:
        load_dotenv(override=True, encoding="utf-8-sig")


_load_env()

from agents import Agent, ModelSettings, Runner, WebSearchTool, gen_trace_id, trace

SEARCHES = 3


class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(
        min_length=3,
        max_length=3,
        description="Exactly three clarifying questions.",
    )


clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=(
        "Given a research query, output exactly THREE short clarifying questions (one sentence each) "
        "to narrow scope before web search. Cover audience/use case, time range, and depth or region/vendor. "
        "Do not answer them."
    ),
    model="gpt-4o-mini",
    output_type=ClarifyingQuestions,
)


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search matters.")
    query: str = Field(description="Search string to run.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        min_length=SEARCHES,
        max_length=SEARCHES,
        description=f"Exactly {SEARCHES} distinct web searches.",
    )


planner_agent = Agent(
    name="PlannerAgent",
    instructions=(
        "You get the user's research query plus three clarifying Q&As. "
        f"Output exactly {SEARCHES} web search queries that cover the clarified intent. "
        "Make them concrete and non-overlapping."
    ),
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)


search_agent = Agent(
    name="SearchAgent",
    instructions=(
        "Use web search for the given term. Return a tight summary under 250 words: bullets OK, "
        "no intro/outro—facts, names, dates. Another agent will merge your notes."
    ),
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)


class ReportData(BaseModel):
    short_summary: str = Field(description="2–3 sentences.")
    report: str = Field(
        description="Body with headings ## Summary, ## Key points, ## Practical takeaways, ## Follow-ups."
    )
    follow_up_questions: list[str] = Field(description="2–4 follow-up research ideas.")


writer_agent = Agent(
    name="WriterAgent",
    instructions=(
        "Synthesize the notes into ~400–700 words using headings "
        "## Summary, ## Key points, ## Practical takeaways, ## Follow-ups. Be specific; note if sources were thin."
    ),
    model="gpt-4o-mini",
    output_type=ReportData,
)


class ResearchManager:
    async def clarify(self, query: str) -> ClarifyingQuestions:
        r = await Runner.run(clarifier_agent, f"Research query:\n{query}")
        return r.final_output_as(ClarifyingQuestions)

    async def plan_searches(self, query: str, questions: list[str], answers: list[str]) -> WebSearchPlan:
        if len(questions) != 3 or len(answers) != 3:
            raise ValueError("Need three questions and three answers.")
        qa = "\n".join(f"Q{i+1}: {q}\nA{i+1}: {a}" for i, (q, a) in enumerate(zip(questions, answers)))
        r = await Runner.run(planner_agent, f"Original query:\n{query}\n\nClarifications:\n{qa}")
        return r.final_output_as(WebSearchPlan)

    async def _one_search(self, item: WebSearchItem) -> str | None:
        msg = f"Search term: {item.query}\nReason: {item.reason}"
        try:
            out = await Runner.run(search_agent, msg)
            return str(out.final_output)
        except Exception:
            return None

    async def perform_searches(self, plan: WebSearchPlan) -> list[str]:
        tasks = [asyncio.create_task(self._one_search(item)) for item in plan.searches]
        notes: list[str] = []
        n = 0
        for coro in asyncio.as_completed(tasks):
            text = await coro
            if text:
                notes.append(text)
            n += 1
            print(f"Search progress: {n}/{len(tasks)}", flush=True)
        return notes

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        msg = f"Original query:\n{query}\n\nResearch notes (from web search):\n{search_results}"
        r = await Runner.run(writer_agent, msg)
        return r.final_output_as(ReportData)

    async def run(self, query: str, questions: list[str], answers: list[str], *, trace_name: str = "Deep research"):
        trace_id = gen_trace_id()
        with trace(trace_name, trace_id=trace_id):
            yield f"Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            yield "Planning searches..."
            plan = await self.plan_searches(query, questions, answers)
            yield f"Running {len(plan.searches)} web searches..."
            notes = await self.perform_searches(plan)
            yield "Writing report..."
            report = await self.write_report(query, notes)
            yield report.report


def _chunks_to_markdown(chunks: list[str]) -> str:
    if not chunks:
        return "_No output._"
    status = "\n\n".join(chunks[:-1])
    return f"### Status\n\n{status}\n\n---\n\n{chunks[-1]}"


def _launch_gradio() -> None:
    import gradio as gr

    async def on_clarify(text: str):
        text = text.strip()
        if not text:
            return "Enter a research query.", None
        out = await ResearchManager().clarify(text)
        lines = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(out.questions))
        body = f"### Clarifying questions\n{lines}\n\nAnswer below, then **Run research**."
        return body, list(out.questions)

    async def on_run(query: str, qs: list | None, a1: str, a2: str, a3: str):
        query = query.strip()
        if not query:
            return "Enter a query and run **Generate questions** first."
        if not qs or len(qs) != 3:
            return "Run **Generate questions** first."
        answers = [
            a1.strip() or "(not specified)",
            a2.strip() or "(not specified)",
            a3.strip() or "(not specified)",
        ]
        chunks: list[str] = []
        async for part in ResearchManager().run(query, qs, answers):
            chunks.append(part)
        return _chunks_to_markdown(chunks)

    def sync_clarify(q):
        return asyncio.run(on_clarify(q))

    def sync_run(q, qs, a1, a2, a3):
        return asyncio.run(on_run(q, qs, a1, a2, a3))

    with gr.Blocks(title="Deep research") as ui:
        gr.Markdown("# Deep research\nQuestions → web search → report.")
        saved_qs = gr.State(None)
        qbox = gr.Textbox(label="Research query", placeholder="e.g. AKS hardening priorities for 2026")
        b1 = gr.Button("1. Generate questions", variant="secondary")
        clarify_md = gr.Markdown()
        a1 = gr.Textbox(label="Answer 1")
        a2 = gr.Textbox(label="Answer 2")
        a3 = gr.Textbox(label="Answer 3")
        b2 = gr.Button("2. Run research", variant="primary")
        out = gr.Markdown()

        b1.click(sync_clarify, [qbox], [clarify_md, saved_qs])
        b2.click(sync_run, [qbox, saved_qs, a1, a2, a3], [out])

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    _launch_gradio()
