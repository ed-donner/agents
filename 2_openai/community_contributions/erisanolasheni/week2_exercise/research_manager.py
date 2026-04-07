"""Orchestrates clarify → plan → search → optional expansion → write → evaluate → optional revise → email."""

from __future__ import annotations

import asyncio
import os

from agents import Runner, gen_trace_id, trace

from clarify_agent import clarify_agent
from config import get_run_config
from email_agent import email_agent
from evaluator_agent import EvaluationBrief, evaluator_agent
from expansion_agent import expansion_agent
from planner_agent import planner_agent
from schemas import ClarifyingQuestions, FollowUpPlan, WebSearchItem, WebSearchPlan
from search_agent import search_agent
from writer_agent import ReportData, writer_agent


class ResearchManager:
    def __init__(self) -> None:
        self._rc = get_run_config()

    async def clarify(self, query: str) -> str:
        result = await Runner.run(
            clarify_agent,
            f"Research topic:\n{query}",
            run_config=self._rc,
        )
        cq = result.final_output_as(ClarifyingQuestions)
        lines = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(cq.questions))
        return (
            "### Clarifying questions\n\n"
            f"{lines}\n\n"
            "_Answer these in the box below, then click **Run deep research**._"
        )

    async def run(self, query: str, clarification_answers: str):
        trace_id = gen_trace_id()
        with trace("Week2 deep research", trace_id=trace_id):
            yield f"**Trace:** https://platform.openai.com/traces/trace?trace_id={trace_id}"
            enriched = (
                f"Original query:\n{query}\n\n"
                "User clarifications (answers to the three questions):\n"
                f"{clarification_answers or '(none provided)'}\n"
            )
            yield "**Planning** initial searches…"
            plan = await self._plan(enriched)
            yield f"**Searching** ({len(plan.searches)} queries)…"
            results = await self._search_batch(plan.searches)
            yield "**Expansion agent** deciding on follow-up searches…"
            extra_items = await self._maybe_expand(enriched, results)
            if extra_items:
                yield f"**Follow-up search** ({len(extra_items)} queries)…"
                more = await self._search_batch(extra_items)
                results.extend(more)
            else:
                yield "**No** follow-up searches needed."
            yield "**Writing** draft report…"
            report = await self._write(enriched, results)
            yield "**Evaluator** reviewing…"
            evaluation = await self._evaluate(enriched, report)
            yield f"_Evaluator:_ {evaluation.comment}"
            if not evaluation.adequate and evaluation.revision_brief.strip():
                yield "**Revising** from evaluator feedback…"
                report = await self._revise(enriched, results, report, evaluation.revision_brief)
            if os.getenv("SKIP_EMAIL", "").lower() in ("1", "true", "yes"):
                yield "_Email skipped (`SKIP_EMAIL`)._"
            else:
                yield "**Email** step (SendGrid if configured)…"
                await self._email(report)
            yield "\n\n---\n\n" + report.markdown_report

    async def _plan(self, brief: str) -> WebSearchPlan:
        result = await Runner.run(planner_agent, brief, run_config=self._rc)
        return result.final_output_as(WebSearchPlan)

    async def _maybe_expand(self, brief: str, summaries: list[str]) -> list[WebSearchItem]:
        joined = "\n---\n".join(summaries[:30])
        payload = f"{brief}\n\nSummaries so far:\n{joined}"
        result = await Runner.run(expansion_agent, payload, run_config=self._rc)
        plan = result.final_output_as(FollowUpPlan)
        if not plan.need_follow_up:
            return []
        return plan.searches[:3]

    async def _search_batch(self, items: list[WebSearchItem]) -> list[str]:
        tasks = [asyncio.create_task(self._one_search(it)) for it in items]
        out: list[str] = []
        for coro in asyncio.as_completed(tasks):
            text = await coro
            if text:
                out.append(text)
        return out

    async def _one_search(self, item: WebSearchItem) -> str | None:
        prompt = f"Search term: {item.query}\nReason: {item.reason}"
        try:
            result = await Runner.run(search_agent, prompt, run_config=self._rc)
            return str(result.final_output)
        except Exception:
            return None

    async def _write(self, brief: str, snippets: list[str]) -> ReportData:
        payload = f"{brief}\n\nResearch notes:\n" + "\n---\n".join(snippets)
        result = await Runner.run(writer_agent, payload, run_config=self._rc)
        return result.final_output_as(ReportData)

    async def _evaluate(self, brief: str, report: ReportData) -> EvaluationBrief:
        payload = f"Brief:\n{brief}\n\nReport markdown:\n{report.markdown_report}"
        result = await Runner.run(evaluator_agent, payload, run_config=self._rc)
        return result.final_output_as(EvaluationBrief)

    async def _revise(
        self,
        brief: str,
        snippets: list[str],
        previous: ReportData,
        revision_brief: str,
    ) -> ReportData:
        payload = (
            f"{brief}\n\nResearch notes:\n"
            + "\n---\n".join(snippets)
            + "\n\nPrevious report (improve, do not lose factual content):\n"
            + previous.markdown_report
            + "\n\nRequired revisions:\n"
            + revision_brief
        )
        result = await Runner.run(writer_agent, payload, run_config=self._rc)
        return result.final_output_as(ReportData)

    async def _email(self, report: ReportData) -> None:
        await Runner.run(email_agent, report.markdown_report, run_config=self._rc)
