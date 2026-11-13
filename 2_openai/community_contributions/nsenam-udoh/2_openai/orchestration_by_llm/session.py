import logging
import re
import time
from collections.abc import Sequence

from agents import Runner

from clarifier_agent import ClarifyingQuestion
from manager_agent import ManagerTurn, RunContext, manager
from writer_agent import uncited_sentences

logger = logging.getLogger(__name__)

MAX_CLARIFICATION_ROUNDS = 3
MAX_TOTAL_SEARCHES = 9
MAX_ANSWER_LENGTH = 1000
MAX_PASSES = 3  # shortcut: pass cap bounds cost, no token budget, upgrade if latency matters
CLARIFICATION_LIMIT_MESSAGE = "Clarification limit reached"
FINAL_CORRECTION = (
    "Your final response was rejected because the required workflow is incomplete. "
    "Run at least one search and produce a non-empty report after planning, "
    "synthesizing, writing, evaluating, and notifying. Then return final."
)
CITATION_CORRECTION = (
    "Your report has factual sentences with no [n] citation. Call the writer tool again "
    "with the same research, then return final with the complete rewritten report. "
    "Every factual sentence must end with [n] matching a source number. Uncited sentences:"
)


class ManagerSession:
    def __init__(self, max_searches: int = MAX_TOTAL_SEARCHES):
        self.context = RunContext(max_searches=max_searches)
        self.status: str | None = None
        self.questions: list[ClarifyingQuestion] = []
        self.turn_number = 0
        self._input = None

    async def start(self, query: str) -> ManagerTurn:
        if self.status is not None:
            raise RuntimeError("This session has already started")
        return await self._run(query)

    async def answer(self, answers: Sequence[str]) -> ManagerTurn:
        if self.status in {"final", "exhausted"}:
            raise RuntimeError("Cannot answer after the session has ended")
        if self.status != "need_answers":
            raise RuntimeError("There are no clarification questions to answer")

        supplied = list(answers)[: len(self.questions)]
        aligned = supplied + [""] * (len(self.questions) - len(supplied))
        answer_lines = []
        for index, (question, answer) in enumerate(zip(self.questions, aligned), start=1):
            value = (answer or "")[:MAX_ANSWER_LENGTH].strip() or "No answer"
            answer_lines.append(f"{index}. {question.question}\nAnswer: {value}")
        message = "Clarification answers:\n" + "\n".join(answer_lines)
        next_input = self._input + [{"role": "user", "content": message}]
        return await self._run(next_input)

    async def _run(self, run_input) -> ManagerTurn:
        correction_sent = False
        citation_passes = 1
        best_turn = None
        best_uncited_count = None
        while True:
            started = time.perf_counter()
            result = await Runner.run(
                manager,
                run_input,
                context=self.context,
                max_turns=20,
            )
            self.turn_number += 1
            self._input = result.to_input_list()
            turn = result.final_output
            self._log_turn(turn.status, result, started)

            invalid_final = turn.status == "final" and (
                self.context.searches_used == 0 or not turn.report
            )
            if invalid_final and not correction_sent:
                correction_sent = True
                run_input = self._input + [{"role": "user", "content": FINAL_CORRECTION}]
                continue
            if invalid_final:
                return self._accept(
                    ManagerTurn(
                        status="exhausted",
                        report="Manager could not complete the required research workflow",
                    )
                )
            if turn.status == "final":
                uncited = uncited_sentences(turn.report)
                if best_turn is None or len(uncited) < best_uncited_count:
                    best_turn = turn
                    best_uncited_count = len(uncited)
                if uncited and citation_passes < MAX_PASSES and turn is best_turn:
                    citation_passes += 1
                    retry_content = (
                        CITATION_CORRECTION
                        + f"\n\nLatest draft:\n{turn.report}"
                        + "\n\nSentences still uncited:\n"
                        + "\n".join(f"- {sentence}" for sentence in uncited)
                        + "\n\nMake minimal edits that keep all sections and use only supplied source numbers."
                    )
                    run_input = self._input + [
                        {"role": "user", "content": retry_content}
                    ]
                    continue
                if uncited:
                    logger.warning(
                        "Report still has %d uncited sentences after %d passes",
                        len(uncited),
                        citation_passes,
                    )
                return self._accept(best_turn)
            return self._accept(turn)

    def _accept(self, turn: ManagerTurn) -> ManagerTurn:
        if turn.status == "need_answers":
            if self.context.clarification_rounds >= MAX_CLARIFICATION_ROUNDS:
                turn = ManagerTurn(
                    status="exhausted", report=CLARIFICATION_LIMIT_MESSAGE
                )
            else:
                self.context.clarification_rounds += 1
                self.questions = list(turn.questions)

        if turn.status == "final":
            turn.report = self._finalize_report(turn.report)
        self.status = turn.status
        if turn.status != "need_answers":
            self.questions = []
        return turn

    def _finalize_report(self, markdown_report: str) -> str:
        known_numbers = set(self.context.source_numbers.values())
        body = markdown_report.rstrip()
        report_numbers = {int(number) for number in re.findall(r"\[(\d+)\]", body)}
        for number in sorted(report_numbers - known_numbers):
            logger.warning("Removing unknown citation [%d] from report", number)

        body = re.sub(
            r" ?\[(\d+)\]",
            lambda match: (
                match.group(0) if int(match.group(1)) in known_numbers else ""
            ),
            body,
        )
        if self.context.sources:
            sources = "\n".join(
                f"[{number}] {re.sub(r'\[(\d+)\]', r'\1', source.title)} - {source.url} (read {source.date_read})"
                for number, source in enumerate(self.context.sources, start=1)
            )
        else:
            sources = "No sources found"
        return f"{body}\n\n## Sources\n{sources}"

    def _log_turn(self, status: str, result, started: float) -> None:
        usage = result.context_wrapper.usage
        logger.info(
            "turn=%d | status=%s | input_tokens=%d | output_tokens=%d | time=%.2fs",
            self.turn_number,
            status,
            usage.input_tokens,
            usage.output_tokens,
            time.perf_counter() - started,
        )
