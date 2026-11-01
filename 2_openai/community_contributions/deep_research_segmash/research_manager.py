from agents import Runner, trace, gen_trace_id, SQLiteSession
from clarification_agent import clarification_agent
from manager_agent import manager_agent

class ResearchManager:

    def __init__(self):
        # Interactive clarification state (kept between the UI callback invocations)
        self._session: SQLiteSession = SQLiteSession("xyz")
        self._questions_asked = 0
        self._current_query = ""
        # Single trace id shared by ALL agent calls (clarification + manager).
        self._trace_id = gen_trace_id()

    async def answer(self, choice: str):
        with trace("Reasearch trace", trace_id=self._trace_id):
            print(f"Improving query: {choice} Trace: https://platform.openai.com/traces/trace?trace_id={self._trace_id}")
            yield f"Starting research. Trace: https://platform.openai.com/traces/trace?trace_id={self._trace_id}"
            response = await Runner.run(clarification_agent, choice, session=self._session)
            yield response.final_output

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report.

        NOTE: The clarification stage is interactive and driven through the UI
        """
        
        self._current_query = query
        with trace("Reasearch trace", trace_id=self._trace_id):
            print(f"Starting research for query: {query} Trace: https://platform.openai.com/traces/trace?trace_id={self._trace_id}")
            yield f"Starting research. Trace: https://platform.openai.com/traces/trace?trace_id={self._trace_id}"
            response = await Runner.run(manager_agent, query, session=self._session)
            yield response.final_output




