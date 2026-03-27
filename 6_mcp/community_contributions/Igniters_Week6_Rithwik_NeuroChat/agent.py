import os
import asyncio
from dotenv import load_dotenv
from agents import (
    Agent,
    Runner,
    function_tool,
    GuardrailFunctionOutput,
    InputGuardrail,
    RunContextWrapper,
)
from agents.tracing import set_tracing_export_api_key
from pydantic import BaseModel

from models import ResearchResult
from tools import wiki_search, pubmed_abstracts, semantic_scholar_search

load_dotenv(override=True)

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not found. Check your .env file.")

# Traces at https://platform.openai.com/traces
set_tracing_export_api_key(api_key)


class RelevanceOutput(BaseModel):
    is_neuroscience_related: bool
    reason: str


guardrail_agent = Agent(
    name="Topic Guardrail",
    model="gpt-4o-mini",
    instructions="""
You are a topic classifier. Decide whether the user's message is related to
neuroscience, brain science, cognitive science, psychology, or related medical topics.

Respond with JSON only:
{
  "is_neuroscience_related": true | false,
  "reason": "<one sentence explanation>"
}
""",
    output_type=RelevanceOutput,
)


async def neuroscience_guardrail(
    ctx: RunContextWrapper, agent: Agent, input: str
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    output: RelevanceOutput = result.final_output
    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=not output.is_neuroscience_related,
    )


research_agent = Agent(
    name="Neuroscience Research Agent",
    model="gpt-4.1-mini",
    instructions="""
You are a neuroscience research expert. Use the pubmed_abstracts and
semantic_scholar_search tools to find relevant literature.

Return your answer as a JSON object that matches this schema exactly:
{
  "summary": "2-4 sentence plain-English summary",
  "findings": [{"point": "key finding 1"}, {"point": "key finding 2"}, ...],
  "citations": ["Author (Year). Title. Journal.", ...],
  "pubmed_links": ["https://pubmed.ncbi.nlm.nih.gov/...", ...]
}

Include 3-5 findings and one citation + link per paper.
""",
    tools=[pubmed_abstracts, semantic_scholar_search],
    output_type=ResearchResult,
)


@function_tool
async def research_agent_tool(query: str) -> str:
    """
    Use for research-level neuroscience questions requiring peer-reviewed evidence.
    Fetches from PubMed and Semantic Scholar, then returns a structured summary
    with key findings, citations, and direct paper links.
    """
    result = await Runner.run(research_agent, query)
    research: ResearchResult = result.final_output
    return research.to_markdown()


main_agent = Agent(
    name="NeuroChat Main Agent",
    model="gpt-4.1-mini",
    instructions="""
    You are a helpful neuroscience assistant. Choose the right tool for every question:

    - wiki_search: concept explanations, definitions, background
    (e.g. "What is the hippocampus?", "Explain neuroplasticity")

    - research_agent_tool: questions needing peer-reviewed evidence or citations
    (e.g. "Recent studies on Alzheimer's", "What does the literature say about BDNF?")

    Always pick the most appropriate tool. Be concise, accurate, and friendly.
    If a tool returns an error, explain it clearly and suggest the user rephrase.
    """,
    tools=[wiki_search, research_agent_tool],
    input_guardrails=[InputGuardrail(guardrail_function=neuroscience_guardrail)],
)


async def run_agent(user_input: str, history: list[dict] | None = None) -> str:
    """Run the main agent and return its final text output."""
    messages: list[dict] = list(history or [])
    messages.append({"role": "user", "content": user_input})
    try:
        result = await Runner.run(main_agent, messages)
        return result.final_output
    except Exception as e:
        if "tripwire" in str(e).lower() or "guardrail" in str(e).lower():
            return (
                "That question doesn't appear to be related to neuroscience. "
                "Please ask about brain science, cognition, neurological conditions, "
                "or related topics."
            )
        raise


_TOOL_LABELS: dict[str, str] = {
    "wiki_search":             "Searching Wikipedia...",
    "research_agent_tool":     "Searching research databases...",
    "pubmed_abstracts":        "Fetching PubMed abstracts...",
    "semantic_scholar_search": "Searching Semantic Scholar...",
}


async def run_agent_streamed(user_input: str, history: list[dict] | None = None):
    """
    Async generator yielding (status, answer) tuples.

    - While the agent is running tools: yields (status_string, None)
      so the UI can show a live status line.
    - When the final answer is ready: yields (None, answer_string).
    - On error: yields (None, error_string).

    The agent always calls a tool before producing its final answer, so there
    are no assistant text tokens to stream mid-run. Instead we show meaningful
    tool-call status updates, then reveal the complete answer at the end.
    """
    messages: list[dict] = list(history or [])
    messages.append({"role": "user", "content": user_input})

    try:
        stream = Runner.run_streamed(main_agent, messages)

        async for event in stream.stream_events():
            event_type = getattr(event, "type", "")
            if event_type == "run_item_stream_event":
                item = getattr(event, "item", None)
                item_type = getattr(item, "type", "")

                if item_type == "tool_call_item":
                    tool_name = (
                        getattr(item, "name", None)
                        or getattr(getattr(item, "raw_item", None), "name", None)
                        or ""
                    )
                    label = _TOOL_LABELS.get(tool_name, f"Running {tool_name}...")
                    yield (label, None)

        final = stream.final_output
        yield (None, str(final) if final else "No response received. Please try again.")

    except Exception as e:
        if "tripwire" in str(e).lower() or "guardrail" in str(e).lower():
            yield (None, (
                "That question doesn't appear to be related to neuroscience. "
                "Please ask about brain science, cognition, neurological conditions, "
                "or related topics."
            ))
        else:
            yield (None, f"Agent error: {e}")


if __name__ == "__main__":
    async def _test():
        history: list[dict] = []
        exchanges = [
            "What is the blood-brain barrier?",
            "Can you tell me more about how it breaks down in disease?",
            "Recent research on adult neurogenesis",
            "What is the best pizza in New York?",  # should be blocked
        ]
        for q in exchanges:
            print(f"\n{'='*60}\nQ: {q}\n{'='*60}")
            async for status, answer in run_agent_streamed(q, history):
                if status:
                    print(f"  [{status}]")
                if answer:
                    print(answer)
                    history.append({"role": "user", "content": q})
                    history.append({"role": "assistant", "content": answer})

    asyncio.run(_test())