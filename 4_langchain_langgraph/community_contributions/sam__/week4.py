from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition 
from langchain_community.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_openai import ChatOpenAI

from typing import Annotated, List
from pydantic import BaseModel
import gradio as gr

class AppState(BaseModel):
    messages: Annotated[List, add_messages]

search = GoogleSerperAPIWrapper()
tools = [
    Tool.from_function(
        search.run,
        name="google_search",
        description="Search Google using Serper.dev API"
    )
]
 
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)
 
def assistant_node(state: AppState):
    response = llm_with_tools.invoke(state.messages)
    return {"messages": [response]}

 
graph_builder = StateGraph(AppState)

graph_builder.add_node("assistant", assistant_node)
graph_builder.add_node("tools", ToolNode(tools=tools))

graph_builder.add_conditional_edges(
    "assistant",
    tools_condition
)

graph_builder.add_edge("tools", "assistant")

graph_builder.add_edge(START, "assistant")
graph_builder.add_edge("assistant", END)

graph = graph_builder.compile()

def chat(message, history):
    history = history or []

    state = {
        "messages": history + [
            {"role": "user", "content": message}
        ]
    }

    result = graph.invoke(state)

    return result["messages"][-1].content

gr.ChatInterface(chat).launch()