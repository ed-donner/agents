import asyncio
import time

from agents import Runner, gen_trace_id, trace
from openai.types.responses import ResponseTextDeltaEvent

from evaluate_agent import evaluate_agent
from exceptions import BadInputError, StepError
from input_guardrails import check_query
from planner_agent import planner_agent
from refine_query_agent import refine_query_agent
from search_agent import search_agent
from writer_agent import writer_agent
from schemas import Evaluation, RefinedQuery, WebSearchItem, WebSearchPlan

TRACE_URL = "https://platform.openai.com/traces/trace?trace_id="


class ProgressTracker:

    def __init__(self, steps: list[str]):
        self.steps = steps
        self.done = {}
        self.current = None
        self.failed = None

    def start(self, step: str):
        self.current = step
        self._started_at = time.time()

    def finish(self, step: str):
        elapsed = time.time() - self._started_at
        self.done[step] = elapsed
        self.current = None

    def fail(self, step: str):
        self.failed = step
        self.current = None

    def render(self) -> str:
        lines = []
        for step in self.steps:
            if step in self.done:
                secs = self.done[step]
                lines.append(f"- [x] **{step}** ({secs:.1f}s)")
            elif step == self.current:
                lines.append(f"- [ ] **{step}** ...")
            elif step == self.failed:
                lines.append(f"- [ ] **{step}** FAILED")
            else:
                lines.append(f"- [ ] {step}")
        return "\n".join(lines)


class ResearchManager:

    async def refine_research_question(self, query: str) -> RefinedQuery:
        try:
            result = await Runner.run(refine_query_agent, query)
            return result.final_output_as(RefinedQuery)
        except Exception as exc:
            raise StepError("refine", str(exc)) from exc

    async def plan_web_searches(self, refined_query: str) -> WebSearchPlan:
        try:
            result = await Runner.run(planner_agent, f"Query: {refined_query}")
            return result.final_output_as(WebSearchPlan)
        except Exception as exc:
            raise StepError("plan", str(exc)) from exc

    async def run_single_search(self, item: WebSearchItem) -> str | None:
        payload = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            out = await Runner.run(search_agent, payload)
            return str(out.final_output)
        except Exception:
            return None

    async def collect_search_results(self, plan: WebSearchPlan) -> list[str]:
        tasks = [self.run_single_search(item) for item in plan.searches]
        raw = await asyncio.gather(*tasks)
        return [r for r in raw if r is not None]

    async def evaluate_report(self, report_text: str) -> Evaluation:
        try:
            result = await Runner.run(evaluate_agent, report_text)
            return result.final_output_as(Evaluation)
        except Exception as exc:
            raise StepError("evaluate", str(exc)) from exc

    async def stream_research(self, query: str, *, skip_evaluate: bool = True):
        try:
            query = check_query(query)
        except BadInputError as err:
            yield f"**Blocked:** {err}"
            return

        steps = ["Refine topic", "Plan searches", "Gather evidence", "Write report"]
        if not skip_evaluate:
            steps.append("Evaluate report")
        progress = ProgressTracker(steps)

        trace_id = gen_trace_id()
        total_start = time.time()

        try:
            with trace("Deep research (james-kimani)", trace_id=trace_id):
                yield f"[Trace]({TRACE_URL}{trace_id})\n\n{progress.render()}"

                # Refine
                progress.start("Refine topic")
                yield progress.render()
                refined = await self.refine_research_question(query)
                progress.finish("Refine topic")
                yield progress.render() + f"\n\n> {refined.refined_query}"

                # Plan
                progress.start("Plan searches")
                yield progress.render()
                plan = await self.plan_web_searches(refined.refined_query)
                progress.finish("Plan searches")
                planned = [s.query for s in plan.searches]
                yield progress.render() + f"\n\nSearches: {planned}"

                #Search
                progress.start("Gather evidence")
                yield progress.render()
                evidence = await self.collect_search_results(plan)
                progress.finish("Gather evidence")
                yield progress.render() + f"\n\nCollected {len(evidence)} snippet(s)."

                # Write (streamed)
                progress.start("Write report")
                yield progress.render()
                payload = f"Original query: {refined.refined_query}\nSummarized search results:\n{evidence}"
                report_text = ""
                try:
                    result = Runner.run_streamed(writer_agent, payload)
                    async for event in result.stream_events():
                        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                            report_text += event.data.delta
                            yield progress.render() + f"\n\n---\n\n{report_text}"
                except Exception as exc:
                    raise StepError("write", str(exc)) from exc
                progress.finish("Write report")

                # 5. Evaluate (optional)
                if not skip_evaluate:
                    progress.start("Evaluate report")
                    yield progress.render() + f"\n\n---\n\n{report_text}"
                    ev = await self.evaluate_report(report_text)
                    progress.finish("Evaluate report")
                    yield progress.render() + f"\n\nScore: {ev.score}/100 — {'pass' if ev.is_satisfactory else 'fail'}\n\n{ev.feedback}\n\n---\n\n{report_text}"

                total = time.time() - total_start
                yield progress.render() + f"\n\n**Done in {total:.1f}s**\n\n---\n\n{report_text}"

        except StepError as err:
            progress.fail(err.step)
            yield progress.render() + f"\n\n**{err.step} failed:** {err.reason}"
