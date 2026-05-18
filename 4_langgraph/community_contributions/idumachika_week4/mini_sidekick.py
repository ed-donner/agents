"""
Week 4 — LangGraph Sidekick (assessment / assignment).

Mirrors 4_langgraph/sidekick.py + 4_lab4.ipynb flow without Playwright:
  • State + structured EvaluatorOutput
  • Worker (tool-bound LLM) → ToolNode → Worker → Evaluator → loop until done

Run from repository root (uses root uv.lock / .venv):
  uv run python 4_langgraph/community_contributions/idumachika_week4/mini_sidekick.py

Requires OPENAI_API_KEY in agents/.env. OpenRouter: sk-or-* sets API base automatically.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_experimental.tools import PythonREPLTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

_AGENTS_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_AGENTS_ROOT / ".env")
load_dotenv()


def _chat_llm() -> ChatOpenAI:
    key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("Set OPENAI_API_KEY in agents/.env")
    kwargs: dict = {"model": "gpt-4o-mini", "api_key": key}
    if key.startswith("sk-or-"):
        kwargs["base_url"] = "https://openrouter.ai/api/v1"
    elif base := os.getenv("OPENAI_BASE_URL"):
        kwargs["base_url"] = base
    return ChatOpenAI(**kwargs)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(
        description="Whether the success criteria have been met"
    )
    user_input_needed: bool = Field(
        description="True if more input is needed from the user or the assistant is stuck"
    )


class MiniSidekick:
    """LangGraph sidekick: Wikipedia + Python REPL tools, evaluator loop (Week 4 pattern)."""

    def __init__(self) -> None:
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools: List[Any] = []
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()

    def setup(self) -> None:
        wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        python_repl = PythonREPLTool()
        self.tools = [wiki, python_repl]

        worker_llm = _chat_llm()
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = _chat_llm()
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        self._build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
You keep working until you have a question for the user or the success criteria is met.
You can search Wikipedia and run short Python snippets (use print() for output).
The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success criteria:
{state["success_criteria"]}

Reply either with a clear question for the user (e.g. "Question: ...") or your final answer."""

        if state.get("feedback_on_work"):
            system_message += f"""
Your previous answer was rejected. Feedback:
{state["feedback_on_work"]}
Improve your response or ask a focused question."""

        raw = list(state["messages"])
        new_msgs: List[Any] = []
        found = False
        for message in raw:
            if isinstance(message, SystemMessage):
                new_msgs.append(SystemMessage(content=system_message))
                found = True
            else:
                new_msgs.append(message)
        if not found:
            new_msgs = [SystemMessage(content=system_message)] + new_msgs

        response = self.worker_llm_with_tools.invoke(new_msgs)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        lines = ["Conversation:\n"]
        for m in messages:
            if isinstance(m, HumanMessage):
                lines.append(f"User: {m.content}\n")
            elif isinstance(m, AIMessage):
                lines.append(f"Assistant: {m.content or '[tool calls]'}\n")
        return "".join(lines)

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content or ""
        system_message = """You evaluate whether the Assistant completed the user's task.
Respond with feedback, whether success criteria are met, and whether user input is needed."""

        user_message = f"""{self.format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Assistant's latest response:
{last_response}

If the Assistant used tools appropriately, give the benefit of the doubt."""

        if state.get("feedback_on_work"):
            user_message += f"\nPrior feedback: {state['feedback_on_work']}\n"

        eval_result = self.evaluator_llm_with_output.invoke(
            [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ]
        )
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    def _build_graph(self) -> None:
        gb = StateGraph(State)
        gb.add_node("worker", self.worker)
        gb.add_node("tools", ToolNode(tools=self.tools))
        gb.add_node("evaluator", self.evaluator)
        gb.add_conditional_edges(
            "worker",
            self.worker_router,
            {"tools": "tools", "evaluator": "evaluator"},
        )
        gb.add_edge("tools", "worker")
        gb.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", "END": END},
        )
        gb.add_edge(START, "worker")
        self.graph = gb.compile(checkpointer=self.memory)

    def run_superstep(
        self, message: str, success_criteria: str, history: List[dict]
    ) -> List[dict]:
        config = {"configurable": {"thread_id": self.sidekick_id}}
        crit = success_criteria or "The answer should be clear, accurate, and complete."
        state: State = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": crit,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = self.graph.invoke(state, config=config)
        msgs = result["messages"]
        reply_text = msgs[-2].content if len(msgs) >= 2 else ""
        feedback_text = msgs[-1].content if msgs else ""
        user_msg = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": reply_text}
        feedback = {"role": "assistant", "content": feedback_text}
        return history + [user_msg, reply, feedback]

    def reset(self) -> None:
        self.sidekick_id = str(uuid.uuid4())


def main() -> None:
    import gradio as gr

    sk_state: List[Optional[MiniSidekick]] = [None]

    def ensure() -> MiniSidekick:
        if sk_state[0] is None:
            sk = MiniSidekick()
            sk.setup()
            sk_state[0] = sk
        return sk_state[0]

    def process(message: str, success_criteria: str, history: List):
        history = history or []
        sk = ensure()
        return sk.run_superstep(message, success_criteria, list(history))

    def reset_all():
        sk_state[0] = None
        sk = MiniSidekick()
        sk.setup()
        sk_state[0] = sk
        return "", "", []

    with gr.Blocks(title="Mini Sidekick (Week 4)") as ui:
        gr.Markdown(
            "## Week 4 — LangGraph mini sidekick\n"
            "Worker → tools (Wikipedia, Python) → evaluator loop. "
            "Set **success criteria**, send a task, click **Go**."
        )
        chat = gr.Chatbot(label="Chat", height=360, type="messages")
        msg = gr.Textbox(label="Task", placeholder="What should the sidekick do?")
        crit = gr.Textbox(
            label="Success criteria",
            placeholder="How will you judge a good answer?",
        )
        with gr.Row():
            reset_btn = gr.Button("Reset")
            go_btn = gr.Button("Go", variant="primary")

        go_btn.click(process, [msg, crit, chat], [chat])
        msg.submit(process, [msg, crit, chat], [chat])
        reset_btn.click(reset_all, [], [msg, crit, chat])

    ui.launch(inbrowser=True)


if __name__ == "__main__":
    main()
