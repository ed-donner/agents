from __future__ import annotations

from collections.abc import Callable

from agents import Runner, gen_trace_id, trace
from agents.clarifier import clarifier_agent
from agents.evaluator import evaluator_agent
from agents.orchestrator import orchestrator_agent
from agents.researcher import researcher_agent
from agents.writer import writer_agent
from core.state import (
    AllowedAction,
    ClarificationQuestions,
    EvaluationResult,
    FinalReport,
    OrchestratorDecision,
    ResearchResult,
    ResearchState,
)


AnswerProvider = Callable[[list[str]], list[str]]
EventHandler = Callable[[str], None]


class DeepResearchRuntime:
    def __init__(self, max_iterations: int = 2, max_searches: int = 6):
        self.max_iterations = max_iterations
        self.max_searches = max_searches

    async def run(
        self,
        query: str,
        answer_provider: AnswerProvider,
        event_handler: EventHandler | None = None,
    ) -> ResearchState:
        state = ResearchState(
            original_query=query,
            max_iterations=self.max_iterations,
            max_searches=self.max_searches,
        )

        trace_id = gen_trace_id()
        self._emit(f"Trace: {trace_id}", event_handler)

        with trace("Agentic deep research", trace_id=trace_id):
            while True:
                decision = await self._decide_next_action(state)
                action = self._resolve_next_action(decision, state)

                self._emit(f"Next action: {action}", event_handler)

                if action == "clarify":
                    await self._run_clarification(state, answer_provider, event_handler)
                elif action == "research":
                    await self._run_research(state, event_handler)
                elif action == "evaluate":
                    await self._run_evaluation(state, event_handler)
                elif action == "write_report":
                    await self._run_writer(state, event_handler)
                elif action == "stop":
                    break

                if state.final_report is not None:
                    break

            return state

    async def _decide_next_action(self, state: ResearchState) -> OrchestratorDecision:
        prompt = (
            "Choose the next action for this deep research workflow.\n\n"
            f"{state.summary_for_agent()}\n"
        )
        result = await Runner.run(orchestrator_agent, prompt)
        return result.final_output_as(OrchestratorDecision)

    async def _run_clarification(
        self,
        state: ResearchState,
        answer_provider: AnswerProvider,
        event_handler: EventHandler | None,
    ) -> None:
        self._emit("Generating clarifying questions...", event_handler)
        result = await Runner.run(clarifier_agent, state.original_query)
        clarifications = result.final_output_as(ClarificationQuestions)
        state.clarification_questions = clarifications.questions
        state.clarification_answers = answer_provider(clarifications.questions)

    async def _run_research(
        self,
        state: ResearchState,
        event_handler: EventHandler | None,
    ) -> None:
        remaining_searches = max(state.max_searches - state.search_count, 0)
        focus = self._research_focus(state)
        prompt = (
            f"Original query: {state.original_query}\n"
            f"Clarification answers: {state.clarification_answers}\n"
            f"Current focus: {focus}\n"
            f"Remaining search budget: {remaining_searches}\n"
            "Perform focused research within the remaining budget."
        )

        self._emit("Running research pass...", event_handler)
        result = await Runner.run(researcher_agent, prompt)
        research = result.final_output_as(ResearchResult)
        state.research_results.append(research)
        state.iteration_count += 1
        state.search_count += len(research.search_queries)

    async def _run_evaluation(
        self,
        state: ResearchState,
        event_handler: EventHandler | None,
    ) -> None:
        latest_research = state.latest_research()
        prompt = (
            f"Original query: {state.original_query}\n"
            f"Clarification answers: {state.clarification_answers}\n"
            f"Latest research result: {latest_research.model_dump_json(indent=2) if latest_research else 'none'}\n"
            f"Current unresolved gaps: {state.unresolved_gaps()}\n"
            f"Remaining iterations: {state.max_iterations - state.iteration_count}\n"
            f"Remaining search budget: {state.max_searches - state.search_count}\n"
        )

        self._emit("Evaluating research quality...", event_handler)
        result = await Runner.run(evaluator_agent, prompt)
        evaluation = result.final_output_as(EvaluationResult)
        state.evaluator_feedback.append(evaluation)

    async def _run_writer(
        self,
        state: ResearchState,
        event_handler: EventHandler | None,
    ) -> None:
        prompt = (
            f"Original query: {state.original_query}\n"
            f"Clarification answers: {state.clarification_answers}\n"
            f"Research results: {[item.model_dump() for item in state.research_results]}\n"
            f"Evaluation feedback: {[item.model_dump() for item in state.evaluator_feedback]}\n"
        )

        self._emit("Writing final report...", event_handler)
        result = await Runner.run(writer_agent, prompt)
        state.final_report = result.final_output_as(FinalReport)

    def _resolve_next_action(
        self,
        decision: OrchestratorDecision,
        state: ResearchState,
    ) -> AllowedAction:
        proposed = decision.next_action
        fallback = self._fallback_action(state)

        if not self._is_action_allowed(proposed, state):
            state.runtime_notes.append(
                f"Overrode invalid action '{proposed}' with '{fallback}'. Reason: {decision.reason}"
            )
            return fallback

        if proposed == "research" and (
            state.iteration_count >= state.max_iterations
            or state.search_count >= state.max_searches
        ):
            forced = "write_report" if state.research_results else fallback
            state.runtime_notes.append(
                f"Guardrail prevented additional research. Using '{forced}' instead."
            )
            return forced

        return proposed

    def _fallback_action(self, state: ResearchState) -> AllowedAction:
        if not state.clarification_answers:
            return "clarify"
        if not state.research_results:
            return "research"
        if len(state.evaluator_feedback) < len(state.research_results):
            return "evaluate"
        latest_evaluation = state.latest_evaluation()
        if (
            latest_evaluation
            and latest_evaluation.needs_more_research
            and state.iteration_count < state.max_iterations
            and state.search_count < state.max_searches
        ):
            return "research"
        if state.final_report is None:
            return "write_report"
        return "stop"

    def _is_action_allowed(self, action: AllowedAction, state: ResearchState) -> bool:
        if state.final_report is not None:
            return action == "stop"
        if not state.clarification_answers:
            return action == "clarify"
        if not state.research_results:
            return action == "research"
        if len(state.evaluator_feedback) < len(state.research_results):
            return action == "evaluate"
        return action in {"research", "write_report", "stop"}

    def _research_focus(self, state: ResearchState) -> str:
        latest_evaluation = state.latest_evaluation()
        if latest_evaluation and latest_evaluation.recommended_focus.strip():
            return latest_evaluation.recommended_focus.strip()
        if state.unresolved_gaps():
            return state.unresolved_gaps()[0]
        return "Address the main clarified question with diverse, high-signal evidence."

    def _emit(self, message: str, event_handler: EventHandler | None) -> None:
        if event_handler:
            event_handler(message)
