from agents import Runner, trace, gen_trace_id, Agent, function_tool, RunContextWrapper, RunConfig
from search_agent import search_agent
from planner_agent import planner_agent
from writer_agent import writer_agent
from clarify_agent import clarifying_agent, NUMBER_OF_QUESTIONS


@function_tool
async def clarify_tool(context: RunContextWrapper[dict], query: str) -> str:
    """Generate the next clarifying question for the research query. Try to avoid asking questions if possible.
    Returns 'QUESTION:<question>' if more clarification is needed, or 'DONE' if no more questions are needed."""
    history: list[dict] = context.context.get("history", [])
    trace_id: str | None = context.context.get("trace_id")

    if len(history) >= NUMBER_OF_QUESTIONS:
        return "DONE"

    input_parts = [f"Query: {query}"]
    if history:
        input_parts.append("Previous questions and answers:")
        for i, qa in enumerate(history, 1):
            input_parts.append(f"Q{i}: {qa['question']}")
            input_parts.append(f"A{i}: {qa['answer']}")

    run_config = RunConfig(trace_id=trace_id) if trace_id else None
    result = await Runner.run(clarifying_agent, "\n".join(input_parts), run_config=run_config)
    output = result.final_output

    if output is None or isinstance(output, str):
        return "DONE"

    question = getattr(output, "question", "")
    if isinstance(question, str) and question.strip():
        return f"QUESTION:{question.strip()}"
    return "DONE"


RESEARCH_MANAGER_INSTRUCTIONS = """You are a helpful research assistant. Follow these steps exactly in order:

1. Call clarify_tool with the user's research query.
   - If the result starts with "QUESTION:", output ONLY that exact text as your final response and stop immediately. Do not call any other tools.
   - If the result is "DONE", continue to step 2.

2. Call the Planner tool to plan the web searches for the query.

3. Call the Search tool to perform each web search. Call it multiple times as needed for each search item.

4. Hand off to the writer agent with all the collected research results to write the final report."""


def _build_research_manager_agent() -> Agent:
    planner_tool = planner_agent.as_tool("Planner", "Plan the web searches to perform for the query")
    search_tool = search_agent.as_tool("Search", "Perform a single web search")
    return Agent(
        name="ResearchManagerAgent",
        instructions=RESEARCH_MANAGER_INSTRUCTIONS,
        model="gpt-4o-mini",
        tools=[clarify_tool, planner_tool, search_tool],
        handoffs=[writer_agent],
    )


class ResearchManager:

    async def run(self, query: str, history: list[dict] | None = None, trace_id: str | None = None):
        """Run the deep research process, yielding status updates and the final result.

        Yields dicts:
          {"type": "status", "message": str}
          {"type": "clarification", "question": str}
          {"type": "report", "content": str}
        """
        if trace_id is None:
            trace_id = gen_trace_id()
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
        if history is None:
            history = []

        agent = _build_research_manager_agent()

        input_parts = [f"Research query: {query}"]
        if history:
            input_parts.append("Previous clarifying questions and answers:")
            for i, qa in enumerate(history, 1):
                input_parts.append(f"Q{i}: {qa['question']}")
                input_parts.append(f"A{i}: {qa['answer']}")

        # Map call_id -> tool_name to correlate tool_output events back to tool names
        call_id_to_tool: dict[str, str] = {}
        search_count = 0

        with trace("Research trace", trace_id=trace_id):
            result = Runner.run_streamed(
                agent,
                "\n".join(input_parts),
                context={"history": history, "query": query, "trace_id": trace_id},
            )

            async for event in result.stream_events():
                if not hasattr(event, "name") or not hasattr(event, "item"):
                    continue

                if event.name == "tool_called":
                    raw = getattr(event.item, "raw_item", None)
                    tool_name = getattr(raw, "name", None) or ""
                    call_id = getattr(raw, "call_id", None) or getattr(raw, "id", None) or ""
                    if call_id and tool_name:
                        call_id_to_tool[call_id] = tool_name

                    if tool_name == "clarify_tool":
                        yield {"type": "status", "message": "Checking if clarification is needed..."}
                    elif tool_name == "Planner":
                        yield {"type": "status", "message": "Planning searches..."}
                    elif tool_name == "Search":
                        yield {"type": "status", "message": "Performing web search..."}

                elif event.name == "tool_output":
                    raw = getattr(event.item, "raw_item", None)
                    call_id = getattr(raw, "call_id", None) or ""
                    tool_name = call_id_to_tool.get(call_id, "")

                    if tool_name == "Planner":
                        yield {"type": "status", "message": "Searches planned, starting to search..."}
                    elif tool_name == "Search":
                        search_count += 1
                        yield {"type": "status", "message": f"Search {search_count} completed..."}

                elif event.name == "handoff_occurred":
                    yield {"type": "status", "message": "Searches complete, writing report..."}

            final_output = result.final_output
            if isinstance(final_output, str) and "QUESTION:" in final_output:
                question = final_output.split("QUESTION:", 1)[1].strip()
                yield {"type": "clarification", "question": question}
            elif hasattr(final_output, "markdown_report"):
                yield {"type": "report", "content": final_output.markdown_report}
            else:
                yield {"type": "report", "content": str(final_output)}
