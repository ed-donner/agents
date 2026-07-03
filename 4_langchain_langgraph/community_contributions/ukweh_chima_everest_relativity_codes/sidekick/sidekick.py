import os
from typing import Annotated, List, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

# Step 1: Define the State
class State(TypedDict):
    messages: Annotated[list, add_messages]
    plan: str
    review_feedback: str

# Step 2: Define the Nodes
def planner_node(state: State):
    load_dotenv(override=True)
    llm = ChatOpenAI(model="gpt-4o-mini")
    last_message = state["messages"][-1].content
    prompt = f"Based on this request: '{last_message}', create a 3-step execution plan."
    response = llm.invoke(prompt)
    return {"plan": response.content, "messages": [AIMessage(content=f"Plan: {response.content}")]}

def executor_node(state: State):
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = f"Execute this plan: {state['plan']}. Provide the final result."
    response = llm.invoke(prompt)
    return {"messages": [AIMessage(content=f"Execution Result: {response.content}")]}

def reviewer_node(state: State):
    llm = ChatOpenAI(model="gpt-4o-mini")
    last_execution = state["messages"][-1].content
    prompt = f"Review this execution: '{last_execution}'. If it's complete, say 'APPROVED'. Otherwise, suggest improvements."
    response = llm.invoke(prompt)
    return {"review_feedback": response.content, "messages": [AIMessage(content=f"Review: {response.content}")]}

# Step 3: Define Conditional Edge logic
def should_continue(state: State) -> Literal["end", "continue"]:
    if "APPROVED" in state["review_feedback"].upper():
        return "end"
    return "continue"

def main():
    # Step 4: Build the Graph
    builder = StateGraph(State)
    builder.add_node("planner", planner_node)
    builder.add_node("executor", executor_node)
    builder.add_node("reviewer", reviewer_node)
    
    # Step 5: Define the Edges
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "executor")
    builder.add_edge("executor", "reviewer")
    
    builder.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "end": END,
            "continue": "executor"
        }
    )
    
    # Step 6: Compile and Run
    graph = builder.compile()
    
    print("🤖 Advanced LangGraph Sidekick (Planner-Executor-Reviewer) is ready!")
    user_input = "Write a Python script to calculate Fibonacci numbers up to N."
    print(f"User: {user_input}")
    
    inputs = {"messages": [HumanMessage(content=user_input)]}
    for event in graph.stream(inputs):
        for node, value in event.items():
            print(f"\n--- {node.upper()} ---")
            if "messages" in value:
                print(value["messages"][-1].content)

if __name__ == "__main__":
    main()
