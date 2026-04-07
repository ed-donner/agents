"""Research agent node: web search via Tavily + LLM synthesis."""

from langchain_core.messages import HumanMessage, AIMessage
from llm_client import get_llm
from agents.state import AgentState

RESEARCH_SYSTEM = """You are SideKick, a professional AI assistant for a Senior Project Manager at a software development company.

Your research capabilities:
- Synthesize web search results into concise, actionable intelligence
- Provide competitive analysis and market insights relevant to software services
- Summarize industry trends, vendor comparisons, or technology evaluations
- Always cite sources with [title](url) format
- Flag any outdated or low-confidence information

Structure research outputs as:
## Summary
[2–3 sentence executive summary]

## Key Findings
- Finding 1 [source]
- Finding 2 [source]
...

## Implications / Recommendations
[What this means for the user's context]
"""


def research_node(state: AgentState) -> dict:
    """Handles research intent using search results already in tool_data."""
    llm = get_llm(temperature=0.2)
    last_human = next(
        (m for m in reversed(state.messages) if isinstance(m, HumanMessage)), None
    )

    # Build context from search results
    search_context = ""
    results = state.tool_data.get("search_results", [])
    if results:
        lines = ["Web search results:\n"]
        for i, r in enumerate(results, 1):
            lines.append(
                f"{i}. [{r['title']}]({r['url']})\n"
                f"   {r['content']}\n"
            )
        search_context = "\n".join(lines)
    else:
        search_context = "No search results available. Answer from your knowledge."

    user_message = last_human.content if last_human else ""
    full_prompt = f"{RESEARCH_SYSTEM}\n\n{search_context}\n\nUser request: {user_message}"

    response = llm.invoke(full_prompt)
    return {
        "response": response.content,
        "messages": [AIMessage(content=response.content)],
    }
