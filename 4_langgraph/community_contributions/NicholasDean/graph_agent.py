"""Week 4 (LangGraph) deliverable - a minimal tool-using agent as a graph.

The five LangGraph ideas in ~40 lines: a State whose `messages` field uses the add_messages
reducer, a StateGraph with two nodes (worker LLM + ToolNode), a conditional edge that loops
worker -> tools -> worker until the model stops calling tools, and a MemorySaver checkpointer so a
thread_id remembers the conversation. (Week 4's Sidekick adds an evaluator/success-criteria loop on
top of exactly this shape.)

Run: uv run python graph_agent.py     (needs OPENAI_API_KEY)
"""
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[list, add_messages]      # reducer: new messages append, not overwrite


@tool
def word_count(text: str) -> int:
    """Count the words in a piece of text."""
    return len(text.split())


tools = [word_count]
llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)     # the LLM can now emit tool calls


def worker(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


def route(state: State):                          # tool calls pending? run them, else stop
    return "tools" if state["messages"][-1].tool_calls else END


graph = StateGraph(State)
graph.add_node("worker", worker)
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "worker")
graph.add_conditional_edges("worker", route, {"tools": "tools", END: END})
graph.add_edge("tools", "worker")                 # after tools run, back to the worker
app = graph.compile(checkpointer=MemorySaver())   # checkpointer = memory across turns (per thread_id)


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "demo"}}
    for q in ["How many words are in 'the quick brown fox jumps'?", "What did I just ask you?"]:
        out = app.invoke({"messages": [{"role": "user", "content": q}]}, config=config)
        print(f"Q: {q}\nA: {out['messages'][-1].content}\n")
