import logging
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from education_coach.config import get_settings
from education_coach.state import EvaluatorOutput, State

logger = logging.getLogger(__name__)

MAX_EVALUATOR_ITERATIONS = 8


def _model() -> str:
    return get_settings().openai_model


def _openai_llm_kwargs(*, streaming: bool) -> dict:
    s = get_settings()
    kwargs: dict = {
        "model": s.openai_model,
        "temperature": s.openai_temperature,
        "streaming": streaming,
    }
    if s.openai_top_p is not None:
        kwargs["top_p"] = s.openai_top_p
    if s.openai_max_tokens is not None:
        kwargs["max_tokens"] = s.openai_max_tokens
    return kwargs


def make_worker_llm(tools: list):
    streaming = get_settings().openai_worker_streaming
    return ChatOpenAI(**_openai_llm_kwargs(streaming=streaming)).bind_tools(tools)


def make_evaluator_llm():
    return ChatOpenAI(**_openai_llm_kwargs(streaming=False)).with_structured_output(
        EvaluatorOutput
    )


def worker_node(worker_llm, state: State) -> Dict[str, Any]:
    system_message = f"""You are a warm, patient learning coach for high school and university students. Your priority is that they feel helped and understood—not rushed into a generic answer.

Before you teach at length:
- Try to know what they are studying (subject, unit, or course topic) and their level (e.g. Year 10, intro college, beginner).
- If the student did not make subject or level reasonably clear, or they only said hello / something very open-ended, do NOT give a long lesson or call tools yet.
  Reply with 2–4 concrete questions so you can tailor help. Start each question with a separate line beginning exactly with: Question:
  Example topics to cover in those questions: what class or subject, what unit or topic, year/level, what they already tried, what feels stuck.
- Exception: if they ask one narrow, self-contained factual question and scope is obvious, you may answer briefly or use tools—still invite them to share level if useful.

When you have enough context to teach:
- Use examples, analogies, and step-by-step reasoning; label optional "stretch" detail clearly.
- Academic integrity: do NOT complete graded homework or exams for them. Offer hints, guiding questions, outlines, and practice.
- When you use tools (Wikipedia / web search), synthesize in your own words and mention sources briefly.
- When search_course_materials is available, use it for course-specific facts before guessing; cite [SOURCE: ...] tags from tool output when you use those excerpts.

Success criteria for this session:
{state["success_criteria"]}

Reply format:
- Clarification-only turn: several lines, each starting with Question: (no lesson paragraphs before that).
- Full tutoring turn: teach first; close with a brief check-for-understanding or a concrete next step the student can try.
"""

    if state.get("feedback_on_work"):
        system_message += f"""

Your previous answer did not yet satisfy the evaluator. Feedback to address:
{state["feedback_on_work"]}
Improve the answer or ask a precise clarification question."""

    messages = state["messages"]
    found_system_message = False
    for message in messages:
        if isinstance(message, SystemMessage):
            message.content = system_message
            found_system_message = True

    if not found_system_message:
        messages = [SystemMessage(content=system_message)] + list(messages)

    response = worker_llm.invoke(messages)
    return {"messages": [response]}


def worker_router(state: State) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "evaluator"


def format_conversation(messages: List[Any]) -> str:
    lines: List[str] = ["Conversation history:\n"]
    for message in messages:
        if isinstance(message, HumanMessage):
            lines.append(f"Student: {message.content}\n")
        elif isinstance(message, AIMessage):
            text = message.content or "[Tool calls]"
            lines.append(f"Tutor: {text}\n")
    return "".join(lines)


def format_tool_evidence(messages: List[Any]) -> str:
    parts: List[str] = []
    for message in messages:
        if isinstance(message, ToolMessage):
            name = getattr(message, "name", None) or "tool"
            body = (message.content or "")[:8000]
            parts.append(f"--- {name} ---\n{body}")
    return "\n".join(parts) if parts else "(no tool results in this thread)"


def evaluator_node(evaluator_llm, state: State) -> Dict[str, Any]:
    n = int(state.get("evaluator_iterations") or 0)
    if n >= MAX_EVALUATOR_ITERATIONS:
        logger.warning("Evaluator iteration cap (%s) reached", MAX_EVALUATOR_ITERATIONS)
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Evaluator: Maximum quality-review rounds reached for this turn. "
                        "Use the tutor's last reply above, or send a follow-up message to continue."
                    ),
                )
            ],
            "feedback_on_work": state.get("feedback_on_work"),
            "success_criteria_met": True,
            "user_input_needed": False,
            "evaluator_iterations": n,
        }

    last = state["messages"][-1]
    last_response = getattr(last, "content", None) or "[No text content]"

    system_message = """You evaluate whether a tutor response successfully meets the session success criteria.
Be strict about pedagogy: for graded work, accepting a full solution should fail the criteria.

If the student's request was vague or missing subject/level and the tutor replied with focused Question: lines to learn what they study and their level, that is good tutoring: set user_input_needed=true, grounding_ok=true, and success_criteria_met=true so the student can answer—do not demand a full lesson yet.

If the student already gave clear subject and level (or a narrow factual question), expect a substantive reply that meets the criteria (depth, tools when needed, check-for-understanding or next step).

Set grounding_ok to false if the tutor's latest message:
- States course-specific or examinable facts (dates, policy, definitions from readings) without calling tools when needed, or
- Uses search_course_materials excerpts but omits the matching [SOURCE: ...] tags for those claims, or
- Contradicts the tool excerpts below.

Set grounding_ok to true for purely conceptual, Socratic, clarification questions, or general explanations with no unsupported course-specific specifics."""

    tool_block = format_tool_evidence(state["messages"])
    user_message = f"""Conversation so far:
{format_conversation(state["messages"])}

Tool excerpts returned in this thread (may be empty):
{tool_block}

Success criteria:
{state["success_criteria"]}

Evaluate ONLY the tutor's latest message:
{last_response}
"""

    if state.get("feedback_on_work"):
        user_message += (
            f"\nPrior evaluator note (avoid infinite loops): {state['feedback_on_work']}\n"
        )

    evaluator_messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_message),
    ]
    eval_result = evaluator_llm.invoke(evaluator_messages)

    return {
        "messages": [
            AIMessage(
                content=f"Evaluator: {eval_result.feedback}",
            )
        ],
        "feedback_on_work": eval_result.feedback,
        "success_criteria_met": bool(
            eval_result.success_criteria_met and eval_result.grounding_ok
        ),
        "user_input_needed": eval_result.user_input_needed,
        "evaluator_iterations": n + 1,
    }


def route_after_evaluation(state: State) -> str:
    if state["success_criteria_met"] or state["user_input_needed"]:
        return "END"
    return "worker"
