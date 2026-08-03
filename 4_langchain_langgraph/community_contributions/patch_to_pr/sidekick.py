"""LangGraph sidekick: git patch → GitHub-ready PR text with evaluator loop."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

MAX_EVAL_ROUNDS = 5

DEFAULT_SUCCESS_CRITERIA = """The pull request draft must:
1. Include a clear, imperative PR title line under ## PR Title (single line after the heading).
2. Under ## Summary, explain what changed and why for reviewers (not a raw dump of the diff).
3. Under ## Test plan, list concrete steps or commands someone can run to verify the change.
4. Under ## Risks and rollback, mention deployment or data risks if any, and how to roll back if needed.
5. Under ## Breaking changes, explicitly state Yes or No; if Yes, say what breaks and what to do.
6. Stay faithful to the patch: do not invent files, APIs, or behavior not evidenced in the diff. If the patch is ambiguous, ask one specific question in the draft body (the evaluator will treat that as needing user input)."""


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the draft PR text")
    success_criteria_met: bool = Field(description="Whether the success criteria are met")
    user_input_needed: bool = Field(
        description="True if the draft asks for clarification or the patch is too incomplete to draft safely"
    )


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    eval_round: int


def format_conversation(messages: List[Any]) -> str:
    lines: List[str] = ["Conversation:\n"]
    for message in messages:
        if isinstance(message, HumanMessage):
            lines.append(f"User: {message.content}\n")
        elif isinstance(message, AIMessage):
            text = message.content or "[empty]"
            lines.append(f"Assistant: {text}\n")
        elif isinstance(message, dict) and message.get("role") and message.get("content"):
            role = message["role"]
            lines.append(f"{role}: {message['content']}\n")
    return "".join(lines)


def _drafter_node(llm: ChatOpenAI):
    def drafter(state: State) -> Dict[str, Any]:
        system_message = f"""You are a senior engineer turning a code patch into GitHub pull request text.

Follow the success criteria exactly:
{state["success_criteria"]}

Use these markdown headings in order:
## PR Title
(one line title only)

## Summary

## Test plan

## Risks and rollback

## Breaking changes

Write ready-to-paste Markdown. Be concise but specific."""

        if state.get("feedback_on_work"):
            system_message += f"""

Your previous draft did not meet the bar. Revise using this evaluator feedback:
{state["feedback_on_work"]}"""

        messages = state["messages"]
        found = False
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found = True
        if not found:
            messages = [SystemMessage(content=system_message)] + list(messages)

        response = llm.invoke(messages)
        return {"messages": [response]}

    return drafter


def _evaluator_node(llm: ChatOpenAI):
    evaluator_llm = llm.with_structured_output(EvaluatorOutput)

    def evaluator(state: State) -> Dict[str, Any]:
        last = state["messages"][-1]
        last_response = getattr(last, "content", None) or str(last)

        system_message = """You evaluate whether a draft PR meets the user's success criteria.
Be strict about missing test plans, unmentioned breaking changes, or invented details not in the patch."""

        user_message = f"""{format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Draft PR text to evaluate (assistant's last message):
{last_response}
"""

        eval_result = evaluator_llm.invoke(
            [SystemMessage(content=system_message), HumanMessage(content=user_message)]
        )
        eval_round = int(state.get("eval_round") or 0)
        if not eval_result.success_criteria_met and not eval_result.user_input_needed:
            eval_round += 1

        return {
            "messages": [
                AIMessage(content=f"**Evaluator:** {eval_result.feedback}")
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
            "eval_round": eval_round,
        }

    return evaluator


def route_after_eval(state: State) -> str:
    if state.get("success_criteria_met") or state.get("user_input_needed"):
        return "end"
    if int(state.get("eval_round") or 0) >= MAX_EVAL_ROUNDS:
        return "end"
    return "drafter"


def build_graph(model: str = "gpt-4o-mini"):
    worker_llm = ChatOpenAI(model=model, temperature=0.2)
    drafter = _drafter_node(worker_llm)
    evaluator = _evaluator_node(worker_llm)

    graph_builder = StateGraph(State)
    graph_builder.add_node("drafter", drafter)
    graph_builder.add_node("evaluator", evaluator)
    graph_builder.add_edge(START, "drafter")
    graph_builder.add_edge("drafter", "evaluator")
    graph_builder.add_conditional_edges(
        "evaluator",
        route_after_eval,
        {"drafter": "drafter", "end": END},
    )
    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)
