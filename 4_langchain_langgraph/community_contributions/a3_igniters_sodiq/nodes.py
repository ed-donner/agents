import operator
import os
from typing import Annotated, List, TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from langchain_community.utilities import GoogleSerperAPIWrapper
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv(override=True)

serper = GoogleSerperAPIWrapper(serper_api_key=os.getenv("SERPER_API_KEY"))

class Plan(BaseModel):
    steps: List[str] = Field(description="Specific, distinct research tasks to follow, in order.")

class ResearchState(TypedDict):
    input: str                          
    plan: List[str]                   
    results: Annotated[List[str], operator.add] 
    response: str                          
    status: str                            


llm = ChatOpenAI(model="gpt-4o")

@tool
def search_tool(query: str):
    """Search the web for the given query."""
    return serper.run(query)


async def planner_node(state: ResearchState):
    print("--- [Thinking] Planner is creating research steps ---")
    
    status_update = "Planer is thinking..."
    
    planner_prompt = (
        "You are an expert research lead. Create a 3-step research plan for: "
        f"'{state['input']}'. Break it into 3 distinct, actionable tasks that can be performed in parallel."
    )
    
    structured_llm = llm.with_structured_output(Plan)
    plan = await structured_llm.ainvoke(planner_prompt)
    
    return {"plan": plan.steps, "status": status_update}

async def worker_node(task: str):
    print(f"--- [Worker] Researching: {task} ---")
    
    llm_with_tools = llm.bind_tools([search_tool])
    response = await llm_with_tools.ainvoke(f"Research the following task: {task}")
    
    search_result = ""
    for tool_call in response.tool_calls:
        search_result += str(search_tool.invoke(tool_call['args']))

    summary_prompt = f"Summarize the key data from this search result related to {task}: {search_result}"
    summary = await llm.ainvoke(summary_prompt)
    
    return {"results": [f"Task: {task}. Findings: {summary.content}"]}

async def replanner_node(state: ResearchState):    
    summary_prompt = (
        "You are an expert research editor. Synthesize all the findings to "
        f"provide a final answer to the user's query: '{state['input']}'. "
        f"Base it solely on these findings: {state['results']}"
    )
    
    final_summary = await llm.ainvoke(summary_prompt)
    
    return {"response": final_summary.content, "status": "Task Complete."}


def map_tasks_to_workers(state: ResearchState):
    return [Send("worker_node", task) for task in state["plan"]]


workflow = StateGraph(ResearchState)

workflow.add_node("planner", planner_node)
workflow.add_node("worker_node", worker_node)
workflow.add_node("replanner", replanner_node)

workflow.add_edge(START, "planner")

workflow.add_conditional_edges("planner", map_tasks_to_workers, ["worker_node"])

workflow.add_edge("worker_node", "replanner")

workflow.add_edge("replanner", END)

app = workflow.compile()
