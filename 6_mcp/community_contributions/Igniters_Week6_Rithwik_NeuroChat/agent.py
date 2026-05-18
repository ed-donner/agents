
import os
import sys
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
from agents.mcp import MCPServerStdio
from agents.tracing import set_tracing_export_api_key
from pydantic import BaseModel

from models import ResearchResult

load_dotenv(override=True)


api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not found. Check your .env file.")

# Traces appear at https://platform.openai.com/traces
set_tracing_export_api_key(api_key)

mcp_server = MCPServerStdio(
    params={
        "command": sys.executable,
        "args": ["mcp_server.py"],
    },
    cache_tools_list=True,
)


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
    model="gpt-4o-mini",
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
    mcp_servers=[mcp_server],
    output_type=ResearchResult,
)


@function_tool
async def research_agent_tool(query: str) -> str:
    """
    Use for research-level neuroscience questions requiring peer-reviewed evidence.
    Fetches from PubMed and Semantic Scholar via MCP, returns a structured summary
    with key findings, citations, and direct paper links.
    """
    result = await Runner.run(research_agent, query)
    research: ResearchResult = result.final_output
    return research.to_markdown()


main_agent = Agent(
    name="NeuroChat Main Agent",
    model="gpt-4o-mini",
    instructions="""
You are a helpful neuroscience assistant. Choose the right tool for every question:

- **wiki_search** -- concept explanations, definitions, background
  (e.g. "What is the hippocampus?", "Explain neuroplasticity")

- **research_agent_tool** -- questions needing peer-reviewed evidence or citations
  (e.g. "Recent studies on Alzheimer's", "What does the literature say about BDNF?")

Always pick the most appropriate tool. Be concise, accurate, and friendly.
If a tool returns an error, explain it clearly and suggest the user rephrase.
""",
    mcp_servers=[mcp_server],
    tools=[research_agent_tool],
    input_guardrails=[InputGuardrail(guardrail_function=neuroscience_guardrail)],
)


_TOOL_LABELS: dict[str, str] = {
    "wiki_search":             "Searching Wikipedia...",
    "research_agent_tool":     "Searching research databases...",
    "pubmed_abstracts":        "Fetching PubMed abstracts...",
    "semantic_scholar_search": "Searching Semantic Scholar...",
}


async def run_agent(user_input: str, history: list[dict] | None = None) -> str:
    """Non-streaming entry point."""
    messages = list(history or [])
    messages.append({"role": "user", "content": user_input})
    async with mcp_server:
        try:
            result = await Runner.run(main_agent, messages)
            return result.final_output
        except Exception as e:
            if "tripwire" in str(e).lower() or "guardrail" in str(e).lower():
                return (
                    "That question doesn't appear to be related to neuroscience. "
                    "Please ask about brain science, cognition, or neurological conditions."
                )
            raise


async def run_agent_streamed(user_input: str, history: list[dict] | None = None):
    """
    Async generator yielding (status, text_chunk) tuples.
    The MCP server subprocess is kept alive for the duration of the stream.

    Yields:
      (status_string, None)  when a tool call starts
      (None, delta_string)   for each assistant text token
    """
    messages = list(history or [])
    messages.append({"role": "user", "content": user_input})

    try:
        async with mcp_server:
            stream = Runner.run_streamed(main_agent, messages)

            async for event in stream.stream_events():
                event_type = getattr(event, "type", "")

                if event_type == "run_item_stream_event":
                    name = getattr(event, "name", "")
                    if name == "tool_called":
                        item = getattr(event, "item", None)
                        raw = getattr(item, "raw_item", None)
                        tool_name = getattr(raw, "name", "") if raw else ""
                        label = _TOOL_LABELS.get(tool_name, "Working...")
                        yield (label, None)

                elif event_type == "raw_response_event":
                    data = getattr(event, "data", None)
                    if getattr(data, "type", "") == "response.output_text.delta":
                        delta = getattr(data, "delta", "")
                        if delta:
                            yield (None, delta)

    except Exception as e:
        if "tripwire" in str(e).lower() or "guardrail" in str(e).lower():
            yield (None, (
                "That question doesn't appear to be related to neuroscience. "
                "Please ask about brain science, cognition, or neurological conditions."
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
            "What is the best pizza in New York?",
        ]
        for q in exchanges:
            print(f"\n{'='*60}\nQ: {q}\n{'='*60}")
            full = ""
            async for status, chunk in run_agent_streamed(q, history):
                if status:
                    print(f"  [{status}]")
                if chunk:
                    print(chunk, end="", flush=True)
                    full += chunk
            print()
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": full})

    asyncio.run(_test())