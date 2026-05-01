import logging
from typing import Any, AsyncIterator
from agents import Runner, gen_trace_id, trace
from openai.types.responses import ResponseTextDeltaEvent
from travel_agents.triage_agent import triage_agent
from models.trip_models import TravelContext

logger = logging.getLogger(__name__)


class TravelExpenseManager:
    """
    Personal Travel & Expense Manager.
    """

    def __init__(self, trip_name: str = "My Trip") -> None:
        self.context = TravelContext(trip_name=trip_name)
        self._trace_id: str = gen_trace_id()
        self._input_list: list[Any] = []
        logger.info("TravelExpenseManager initialised. Trace ID: %s", self._trace_id)

    async def stream_chat(self, message: str) -> AsyncIterator[str]:
        """Stream response for a user message."""
        with trace("TravelExpenseManager", trace_id=self._trace_id):
            try:
                input_with_history = self._input_list + [
                    {"role": "user", "content": message}
                ]

                result = Runner.run_streamed(
                    triage_agent,
                    input_with_history,
                    context=self.context,
                    max_turns=25,
                )

                async for event in result.stream_events():
                    if (
                        event.type == "raw_response_event"
                        and isinstance(event.data, ResponseTextDeltaEvent)
                        and event.data.delta
                    ):
                        yield event.data.delta

                self._input_list = result.to_input_list()

            except Exception as exc:
                logger.exception("Unexpected error during chat turn: %s", exc)
                yield (
                    "An unexpected error occurred. Please try again or rephrase your question.\n"
                    f"Details: {type(exc).__name__}: {exc}"
                )
