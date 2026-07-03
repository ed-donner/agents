from __future__ import annotations

import os
import uuid
from typing import Annotated, Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from sidekick_tools import get_tools

load_dotenv(override=True)


class PlanOutput(BaseModel):
    clarified_goal: str = Field(description="Restated user goal in one sentence.")
    steps: list[str] = Field(description="Short ordered plan to solve the task.")


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Concise feedback on the latest assistant answer.")
    success_criteria_met: bool = Field(description="True if success criteria are met.")
    user_input_needed: bool = Field(description="True if the user must clarify something.")


class SidekickState(TypedDict):
    messages: Annotated[list[Any], add_messages]
    success_criteria: str
    plan: list[str]
    clarified_goal: str
    feedback_on_work: str | None
    success_criteria_met: bool
    user_input_needed: bool
    iterations: int
    final_answer: str | None
    action_card: str | None


class Sidekick:
    def __init__(self, model: str | None = None) -> None:
        selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        tools = get_tools()

        llm = ChatOpenAI(model=selected_model)
        self.worker_llm = llm.bind_tools(tools)
        self.planner_llm = llm.with_structured_output(PlanOutput)
        self.evaluator_llm = llm.with_structured_output(EvaluatorOutput)
        self.coach_llm = llm

        self.thread_id = str(uuid.uuid4())
        self.graph = self._build_graph(tools, MemorySaver())

    def _planner(self, state: SidekickState) -> dict[str, Any]:
        messages = [
            SystemMessage(
                content=(
                    "You are a planning assistant. Build a short practical plan (3-6 steps) "
                    "for the user's request."
                )
            ),
            HumanMessage(content=state["messages"][-1].content),
        ]
        plan = self.planner_llm.invoke(messages)
        return {"plan": plan.steps, "clarified_goal": plan.clarified_goal}

    def _worker(self, state: SidekickState) -> dict[str, Any]:
        system_prompt = (
            "You are a powerful AI sidekick. Use tools when helpful.\n"
            f"Goal: {state['clarified_goal']}\n"
            f"Plan: {state['plan']}\n"
            f"Success criteria: {state['success_criteria']}\n"
            "Return the final answer when complete. If blocked, ask one clear question."
        )
        if state.get("feedback_on_work"):
            system_prompt += f"\nEvaluator feedback to address: {state['feedback_on_work']}"

        response = self.worker_llm.invoke(
            [SystemMessage(content=system_prompt)] + state["messages"]
        )

        final_answer = state.get("final_answer")
        if isinstance(response, AIMessage) and response.content:
            final_answer = str(response.content)

        return {
            "messages": [response],
            "iterations": state["iterations"] + 1,
            "final_answer": final_answer,
        }

    @staticmethod
    def _worker_router(state: SidekickState) -> str:
        last_message = state["messages"][-1]
        return "tools" if getattr(last_message, "tool_calls", None) else "evaluator"

    def _evaluator(self, state: SidekickState) -> dict[str, Any]:
        assistant_answer = state.get("final_answer") or ""
        eval_result = self.evaluator_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "You evaluate whether the assistant answer meets the user's success criteria."
                    )
                ),
                HumanMessage(
                    content=(
                        f"Success criteria:\n{state['success_criteria']}\n\n"
                        f"Assistant answer:\n{assistant_answer}"
                    )
                ),
            ]
        )
        return {
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    @staticmethod
    def _evaluation_router(state: SidekickState) -> str:
        if state["success_criteria_met"] or state["user_input_needed"] or state["iterations"] >= 4:
            return "coach"
        return "worker"

    def _coach(self, state: SidekickState) -> dict[str, Any]:
        answer = state.get("final_answer") or "No answer was produced."
        card = self.coach_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "Create a concise markdown action card from the assistant answer.\n"
                        "Use exactly these headings: ## Outcome, ## Checklist, ## Risks, ## Next Prompt."
                    )
                ),
                HumanMessage(content=answer),
            ]
        )
        return {"action_card": card.content}

    def _build_graph(self, tools: list[Any], memory: MemorySaver):
        builder = StateGraph(SidekickState)
        builder.add_node("planner", self._planner)
        builder.add_node("worker", self._worker)
        builder.add_node("tools", ToolNode(tools=tools))
        builder.add_node("evaluator", self._evaluator)
        builder.add_node("coach", self._coach)

        builder.add_edge(START, "planner")
        builder.add_edge("planner", "worker")
        builder.add_conditional_edges(
            "worker", self._worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        builder.add_edge("tools", "worker")
        builder.add_conditional_edges(
            "evaluator",
            self._evaluation_router,
            {"worker": "worker", "coach": "coach"},
        )
        builder.add_edge("coach", END)
        return builder.compile(checkpointer=memory)

    def run_turn(
        self,
        message: str,
        success_criteria: str,
        chat_history: list[dict[str, str]],
    ) -> tuple[list[dict[str, str]], str, str, str]:
        state: SidekickState = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria or "The answer should be clear, correct, and actionable.",
            "plan": [],
            "clarified_goal": "",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "iterations": 0,
            "final_answer": None,
            "action_card": None,
        }
        config = {"configurable": {"thread_id": self.thread_id}}
        result = self.graph.invoke(state, config=config)

        answer = (result.get("final_answer") or "").strip()
        feedback = (result.get("feedback_on_work") or "").strip()
        plan = "\n".join(f"- {step}" for step in result.get("plan", []))
        card = (result.get("action_card") or "").strip()

        updated_history = chat_history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": answer or "I need more details to proceed."},
        ]
        return updated_history, plan, feedback, card
