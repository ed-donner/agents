from agents import Runner, trace, gen_trace_id
from clarification_agent import clarification_agent, ClarificationQuestions
from synthesizer_agent import synthesis_agent, RefinedQuery
from orchestrator_agent import orchestrator_agent


class ResearchManager:

    def __init__(self):
        self._questions: list[str] = []

    async def clarify(self, query: str):
        yield "Analyzing your query..."
        result = await Runner.run(clarification_agent, input=query)
        clarification = result.final_output_as(ClarificationQuestions)

        if clarification.is_clear_enough:
            yield None
        else:
            self._questions = clarification.questions
            yield clarification.questions

    async def run(self, query: str, answers: list[str] | None = None):
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            if answers:
                yield "Refining your query..."
                result = await Runner.run(
                    synthesis_agent,
                    input=self._build_synthesis_input(query, answers)
                )
                query = result.final_output_as(RefinedQuery).refined_query
                yield f"Refined query: {query}"

            yield "Starting research..."
            result = await Runner.run(orchestrator_agent, input=query)
            yield result.final_output

    def _build_synthesis_input(self, query: str, answers: list[str]) -> str:
        qa_pairs = "\n".join(
            f"Q: {q}\nA: {a}" for q, a in zip(self._questions, answers)
        )
        return f"Original query: {query}\n\nClarification Q&A:\n{qa_pairs}"