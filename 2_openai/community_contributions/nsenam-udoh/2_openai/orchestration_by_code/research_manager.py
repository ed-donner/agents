import asyncio
import logging
import re
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from agents import Runner

from clarifier_agent import ClarifyingQuestions, clarifier_agent
from evaluator_agent import EvaluationScore, evaluator_agent
from notify import notify
from planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from search_agent import search_agent
from synthesizer_agent import GapReview, synthesizer_agent
from writer_agent import ReportData, uncited_sentences, writer_agent

logger = logging.getLogger(__name__)

MAX_SEARCHES_PER_ROUND = 3
MAX_FOLLOW_UP_ROUNDS = 2
MAX_TOTAL_SEARCHES = 9
MAX_ANSWER_LENGTH = 1000
MAX_PASSES = 3  # shortcut: pass cap bounds cost, no token budget, upgrade if latency matters


@dataclass(frozen=True)
class Source:
    url: str
    title: str
    date_read: str


@dataclass(frozen=True)
class SearchResult:
    summary: str
    sources: list[Source]


class ResearchManager:
    def __init__(self):
        self.sources: list[Source] = []
        self._source_numbers: dict[str, int] = {}

    async def clarify(self, query: str) -> ClarifyingQuestions:
        result = await self._run_agent("clarify", clarifier_agent, f"Query: {query}")
        return result.final_output

    async def run(self, query: str, answers: Sequence[str] | None = None):
        """Run the research process, yielding status updates and the final report."""
        self.sources.clear()
        self._source_numbers.clear()
        try:
            yield "Planning searches..."
            search_plan = await self.plan_searches(query, answers)
            yield f"Searches planned, starting {len(search_plan.searches)} searches..."

            search_results = await self.perform_searches(search_plan, answers)
            total_searches = len(search_plan.searches)
            yield "Initial searches complete, reviewing research gaps..."
            review = await self.review_gaps(query, search_results, answers)

            rounds = 0
            while (
                review.gaps
                and review.follow_up_searches
                and rounds < MAX_FOLLOW_UP_ROUNDS
                and total_searches < MAX_TOTAL_SEARCHES
            ):
                remaining = MAX_TOTAL_SEARCHES - total_searches
                follow_ups = review.follow_up_searches[:MAX_SEARCHES_PER_ROUND][:remaining]
                rounds += 1
                yield f"Running follow-up search round {rounds}..."
                follow_up_plan = WebSearchPlan(searches=follow_ups)
                search_results.extend(await self.perform_searches(follow_up_plan, answers))
                total_searches += len(follow_ups)
                review = await self.review_gaps(query, search_results, answers)

            if not self.sources:
                yield "No sources found"
            yield "Research complete, writing report..."
            report = await self.write_report(query, search_results, answers)
            yield "Report written, evaluating..."
            evaluation = await self.evaluate_report(report)
            yield f"Evaluation score: {evaluation.score}/10. {evaluation.reason}"

            try:
                notify(report.markdown_report)
            except Exception as exc:
                logger.error("Notification failed: %s", exc)
            yield "Research complete"
            yield report.markdown_report
        except Exception as exc:
            logger.exception("Research run failed")
            yield f"Error during research: {exc}"

    async def plan_searches(
        self, query: str, answers: Sequence[str] | None = None
    ) -> WebSearchPlan:
        input_message = self._query_input(query, answers)
        result = await self._run_agent("plan", planner_agent, input_message)
        plan = result.final_output
        return WebSearchPlan(searches=plan.searches[:MAX_SEARCHES_PER_ROUND])

    async def perform_searches(
        self, search_plan: WebSearchPlan, answers: Sequence[str] | None = None
    ) -> list[str]:
        tasks = [self.search(item, answers) for item in search_plan.searches]
        results = await asyncio.gather(*tasks)
        summaries = []
        for result in results:
            source_numbers = [self._register_source(source) for source in result.sources]
            if not source_numbers:
                summaries.append(result.summary)
                continue
            numbers = ", ".join(f"[{number}]" for number in source_numbers)
            summaries.append(f"{result.summary}\n\nSources for this search: {numbers}")
        return summaries

    async def search(
        self, item: WebSearchItem, answers: Sequence[str] | None = None
    ) -> SearchResult:
        started = time.perf_counter()
        input_message = (
            f"Search term: {item.query}\nReason for searching: {item.reason}\n"
            f"Clarification answers:\n{self._format_answers(answers)}"
        )
        result = await Runner.run(search_agent, input_message)
        self._log_usage("search", started, [result])
        sources = self._extract_sources(result)
        if not sources:
            logger.warning("No URL citation annotations returned for search: %s", item.query)
        return SearchResult(summary=result.final_output, sources=sources)

    @staticmethod
    def _extract_sources(result) -> list[Source]:
        sources = []
        seen_urls = set()
        date_read = date.today().isoformat()
        for response in getattr(result, "raw_responses", []) or []:
            for item in getattr(response, "output", []) or []:
                if getattr(item, "type", None) != "message":
                    continue
                for content in getattr(item, "content", []) or []:
                    for annotation in getattr(content, "annotations", []) or []:
                        if getattr(annotation, "type", None) != "url_citation":
                            continue
                        url = getattr(annotation, "url", "")
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)
                        sources.append(
                            Source(
                                url=url,
                                title=getattr(annotation, "title", "") or "",
                                date_read=date_read,
                            )
                        )
        return sources

    def _register_source(self, source: Source) -> int:
        if source.url in self._source_numbers:
            return self._source_numbers[source.url]
        self.sources.append(source)
        number = len(self.sources)
        self._source_numbers[source.url] = number
        return number

    async def review_gaps(
        self,
        query: str,
        search_results: list[str],
        answers: Sequence[str] | None = None,
    ) -> GapReview:
        input_message = (
            f"{self._query_input(query, answers)}\n"
            f"Summarized search results: {search_results}"
        )
        result = await self._run_agent("synthesize", synthesizer_agent, input_message)
        return result.final_output

    async def write_report(
        self,
        query: str,
        search_results: list[str],
        answers: Sequence[str] | None = None,
    ) -> ReportData:
        source_list = "\n".join(
            f"[{number}] {source.title} - {source.url}"
            for number, source in enumerate(self.sources, start=1)
        ) or "No sources found"
        input_message = (
            f"{self._query_input(query, answers)}\n"
            f"Summarized search results: {search_results}\n"
            f"Numbered source list:\n{source_list}"
        )
        result = await self._run_agent("write", writer_agent, input_message)
        report = result.final_output
        uncited = uncited_sentences(report.markdown_report)
        drafts = [(len(uncited), report)]
        passes = 1
        while uncited and passes < MAX_PASSES:
            previous_uncited_count = len(uncited)
            retry_message = input_message + (
                "\n\nYour previous draft had uncited sentences. Rewrite the full report so every "
                "factual sentence ends with [n] citing a numbered source. Do not drop sections. "
                "Make minimal edits that keep all sections and use only supplied source numbers.\n\n"
                f"Complete latest draft:\n{report.markdown_report}\n\n"
                "These sentences had no citation:\n"
                + "\n".join(f"- {sentence}" for sentence in uncited)
            )
            result = await self._run_agent("write", writer_agent, retry_message)
            report = result.final_output
            passes += 1
            uncited = uncited_sentences(report.markdown_report)
            drafts.append((len(uncited), report))
            if len(uncited) >= previous_uncited_count:
                break
        uncited_count, report = min(drafts, key=lambda draft: draft[0])
        if uncited_count:
            logger.warning(
                "Report still has %d uncited sentences after %d passes", uncited_count, passes
            )
        report.markdown_report = self._finalize_report(report.markdown_report)
        return report

    def _finalize_report(self, markdown_report: str) -> str:
        known_numbers = set(self._source_numbers.values())
        report_numbers = {int(number) for number in re.findall(r"\[(\d+)\]", markdown_report)}
        for number in sorted(report_numbers - known_numbers):
            logger.warning("Report contains unknown citation [%d]", number)

        if self.sources:
            sources = "\n".join(
                f"[{number}] {source.title} - {source.url} (read {source.date_read})"
                for number, source in enumerate(self.sources, start=1)
            )
        else:
            sources = "No sources found"
        return f"{markdown_report.rstrip()}\n\n## Sources\n{sources}"

    async def evaluate_report(self, report: ReportData) -> EvaluationScore:
        result = await self._run_agent("evaluate", evaluator_agent, report.markdown_report)
        return result.final_output

    async def _run_agent(self, name: str, agent, input_message: str):
        started = time.perf_counter()
        result = await Runner.run(agent, input_message)
        self._log_usage(name, started, [result])
        return result

    @staticmethod
    def _log_usage(name: str, started: float, results: list) -> None:
        input_tokens = 0
        output_tokens = 0
        for result in results:
            usage = result.context_wrapper.usage
            input_tokens += usage.input_tokens
            output_tokens += usage.output_tokens
        logger.info(
            "%s | %.2fs | input_tokens=%d | output_tokens=%d",
            name,
            time.perf_counter() - started,
            input_tokens,
            output_tokens,
        )

    @staticmethod
    def _format_answers(answers: Sequence[str] | None) -> str:
        if not answers:
            return "No clarification answers provided."
        return "\n".join(
            f"{index}. {(answer or '')[:MAX_ANSWER_LENGTH].strip() or 'No answer'}"
            for index, answer in enumerate(answers, start=1)
        )

    @classmethod
    def _query_input(cls, query: str, answers: Sequence[str] | None) -> str:
        return f"Original query: {query}\nClarification answers:\n{cls._format_answers(answers)}"
