from agents import Runner, trace, gen_trace_id

from dragents.clarification_agent import clarification_agent
from dragents.research_lead_agent import research_lead_agent
from dragents.research_presenters import (
    format_stream_event,
    merge_supervisor_state,
    render_research_state_messages,
)
from models.models import Clarification, ResearchState

class ResearchManager:

    def build_research_state(
        self,
        query: str,
        clarification: Clarification | None = None,
    ) -> ResearchState:
        """Build the shared state object for the supervisor-driven flow."""
        return ResearchState(
            original_query=query,
            clarification=clarification,
            needs_clarification=clarification is None,
            next_action="clarify" if clarification is None else "plan_searches",
        )

    async def run(self, query: str, clarification: Clarification | None = None):
        """Run the deep reserch process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research Trace", trace_id = trace_id):
            print (f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            if clarification is None:
                print ("Clarifying research.....")
                clarify_query = await self.clarify_search(query)
                yield clarify_query
            else:
                state = self.build_research_state(query, clarification)
                async for item in self.supervise_state_streamed(state):
                    if isinstance(item, str):
                        yield item
                    else:
                        state = item

                for message in render_research_state_messages(query, clarification, state):
                    yield message


    async def clarify_search(self, query:str):
        """Use the clarification_agent to ask clafification questions"""
        print("Clarifying search query")
        result = await Runner.run(clarification_agent, f"Query: {query}")
        print (f"will create clarification {len (result.final_output.clarification_questions)} questions")
        return result.final_output

    async def supervise_state_streamed(self, state: ResearchState):
        """Run the supervisor with streaming and emit progress updates plus final state."""
        result = Runner.run_streamed(
            research_lead_agent,
            state.model_dump_json(indent=2),
        )

        async for event in result.stream_events():
            message = format_stream_event(event)
            if message:
                yield message

        yield merge_supervisor_state(state, result.final_output)
