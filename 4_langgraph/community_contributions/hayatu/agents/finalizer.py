from schema import State, FinalizerOutput
from agents.clarifier import format_conversation
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from db.sql_memory import save_preferences


def finalizer_agent(llm_with_output, state: State) -> dict:
    system_message = f"""You are the FINALIZER agent in a multi-agent Sidekick system.

Your job is to produce a polished, user-facing final answer based on the full conversation and work done.

RULES:
- Summarize the results clearly and concisely.
- Do NOT include internal evaluator feedback or technical details.
- Also extract any user preferences you can infer from this conversation.
  Return them as key-value pairs (e.g. {{"preferred_cuisine": "Italian", "city": "New York"}}).
  Only extract preferences that are clearly stated or strongly implied.
  If none are apparent, return null for extracted_preferences.

CONVERSATION:
{format_conversation(state.messages)}

SUCCESS CRITERIA:
{state.success_criteria}
"""

    result: FinalizerOutput = llm_with_output.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content="Produce the final answer and extract any user preferences."),
    ])

    updates = {
        "final_answer": result.final_answer,
        "messages": [AIMessage(content=result.final_answer)],
    }

    return updates, result.extracted_preferences
