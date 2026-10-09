"""Week 4 capstone (LangGraph) - Sidekick: a worker that is checked by an evaluator until it passes.

The distinctive week-4 shape: a worker LLM (with tools) does the task against a `success_criteria`,
then an EVALUATOR node grades the result with structured output and either ends (criteria met, or it
needs the user) or routes back to the worker with feedback to try again.

State -> reducer (add_messages) -> nodes (worker / tools / evaluator) -> conditional edges -> a
MemorySaver checkpointer for cross-turn memory.

Run: uv run python sidekick.py     (needs OPENAI_API_KEY)
"""
import ast
import operator as op
from pathlib import Path
from typing import Annotated, Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[list, add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str
    success_criteria_met: bool
    user_input_needed: bool          # true if the assistant is stuck and needs the user


# ---- tools (dependency-free, but real) ----
@tool
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression, e.g. '23 * (4 + 5)'."""
    ops = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
           ast.Pow: op.pow, ast.USub: op.neg, ast.Mod: op.mod}

    def ev(n):
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.BinOp):
            return ops[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp):
            return ops[type(n.op)](ev(n.operand))
        raise ValueError("unsupported expression")

    return str(ev(ast.parse(expression, mode="eval").body))


@tool
def save_note(filename: str, content: str) -> str:
    """Save text to a file in the sandbox/ folder."""
    folder = Path(__file__).parent / "sandbox"
    folder.mkdir(exist_ok=True)
    (folder / filename).write_text(content, encoding="utf-8")
    return f"saved sandbox/{filename}"


tools = [calculator, save_note]
worker_llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)
evaluator_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(EvaluatorOutput)


# ---- nodes ----
def worker(state: State):
    system = ("You are a capable assistant completing a task. Use the tools when useful and then "
              f"give a final answer. Your success criteria for this task is:\n{state['success_criteria']}")
    if state.get("feedback_on_work"):
        system += (f"\n\nA previous attempt was rejected. Feedback:\n{state['feedback_on_work']}\n"
                   "Improve your answer so it meets the success criteria.")
    reply = worker_llm.invoke([SystemMessage(content=system)] + state["messages"])
    return {"messages": [reply]}


def evaluator(state: State):
    conversation = "\n".join(f"{m.type}: {m.content}" for m in state["messages"] if m.content)
    result = evaluator_llm.invoke([
        SystemMessage(content="You grade whether an assistant met its success criteria. Be strict "
                              "but fair. Set user_input_needed only if the assistant is truly stuck."),
        HumanMessage(content=f"Success criteria:\n{state['success_criteria']}\n\n"
                             f"Conversation:\n{conversation}\n\nDid the assistant meet the criteria?"),
    ])
    return {"feedback_on_work": result.feedback,
            "success_criteria_met": result.success_criteria_met,
            "user_input_needed": result.user_input_needed}


# ---- routing ----
def worker_router(state: State):
    return "tools" if state["messages"][-1].tool_calls else "evaluator"


def route_after_eval(state: State):
    return END if state["success_criteria_met"] or state["user_input_needed"] else "worker"


graph = StateGraph(State)
graph.add_node("worker", worker)
graph.add_node("tools", ToolNode(tools))
graph.add_node("evaluator", evaluator)
graph.add_edge(START, "worker")
graph.add_conditional_edges("worker", worker_router, {"tools": "tools", "evaluator": "evaluator"})
graph.add_edge("tools", "worker")
graph.add_conditional_edges("evaluator", route_after_eval, {"worker": "worker", END: END})
app = graph.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "demo"}}
    out = app.invoke({
        "messages": [HumanMessage(content="Compute 23 * 47 and save the result to answer.txt.")],
        "success_criteria": "23*47 is computed correctly (1081) and saved to answer.txt via a tool.",
        "feedback_on_work": None, "success_criteria_met": False, "user_input_needed": False,
    }, config=config)
    print("final reply:", out["messages"][-1].content)
    print("success_criteria_met:", out["success_criteria_met"])
