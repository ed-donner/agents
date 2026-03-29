import os
import uuid
from typing import List, Optional, Dict, Any, Annotated

import gradio as gr
from dotenv import load_dotenv

from typing_extensions import TypedDict
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.agents import Tool

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from langchain_community.agent_toolkits import FileManagementToolkit

load_dotenv()


# TOOLS

serper = GoogleSerperAPIWrapper()

def get_tools():
    file_tools = FileManagementToolkit(root_dir="sandbox").get_tools()

    search_tool = Tool(
        name="search",
        func=serper.run,
        description="Search the web"
    )

    wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    python_tool = PythonREPLTool()

    return file_tools + [search_tool, wiki_tool, python_tool]

# STATE

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    plan: Optional[Any]
    final_worker_response: Optional[str]


# MODELS

class PlanOutput(BaseModel):
    list_of_steps: List[str]
    estimated_complexity: str

class EvaluatorOutput(BaseModel):
    feedback: str
    success_criteria_met: bool
    user_input_needed: bool

# SIDEKICK

class Sidekick:
    def __init__(self):
        self.tools = get_tools()
        self.sidekick_id = str(uuid.uuid4())
        self.memory = None

        self.worker_llm = ChatOpenAI(model="gpt-4o")
        self.planner_llm = ChatOpenAI(model="gpt-4o").with_structured_output(PlanOutput)
        self.evaluator_llm = ChatOpenAI(model="gpt-4o").with_structured_output(EvaluatorOutput)

    async def setup(self):
        self.memory = await AsyncSqliteSaver.from_conn_string("sidekick_memory.db").__aenter__()
        await self.build_graph()

 
    # PLANNER
   
    def planner(self, state: State):
        user_input = state["messages"][-1].content

        prompt = f"""
Break this goal into steps:

{user_input}

Criteria:
{state["success_criteria"]}
"""

        plan = self.planner_llm.invoke([HumanMessage(content=prompt)])

        return {
            "messages": [AIMessage(content="Plan created")],
            "plan": plan
        }

   
    # WORKER
    
    def worker(self, state: State):
        plan = state.get("plan")

        system_message = f"""
You help users plan tasks and goals.

Follow this plan:
{plan.list_of_steps if plan else ""}

Criteria:
{state["success_criteria"]}
"""

        messages = [SystemMessage(content=system_message)] + state["messages"]

        response = self.worker_llm.invoke(messages)

        return {
            "messages": [response],
            "final_worker_response": response.content
        }

    def worker_router(self, state: State):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "evaluator"

  
    # EVALUATOR
   
    def evaluator(self, state: State):
        last_response = state["messages"][-1].content

        prompt = f"""
Check if this meets the criteria:

{last_response}

Criteria:
{state["success_criteria"]}
"""

        result = self.evaluator_llm.invoke([HumanMessage(content=prompt)])

        return {
            "messages": [AIMessage(content=result.feedback)],
            "feedback_on_work": result.feedback,
            "success_criteria_met": result.success_criteria_met,
            "user_input_needed": result.user_input_needed
        }

    def route_eval(self, state: State):
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    
    # GRAPH
   
    async def build_graph(self):
        graph = StateGraph(State)

        graph.add_node("planner", self.planner)
        graph.add_node("worker", self.worker)
        graph.add_node("tools", ToolNode(self.tools))
        graph.add_node("evaluator", self.evaluator)

        graph.add_edge(START, "planner")
        graph.add_edge("planner", "worker")

        graph.add_conditional_edges(
            "worker",
            self.worker_router,
            {"tools": "tools", "evaluator": "evaluator"}
        )

        graph.add_edge("tools", "worker")

        graph.add_conditional_edges(
            "evaluator",
            self.route_eval,
            {"worker": "worker", "END": END}
        )

        self.graph = graph.compile(checkpointer=self.memory)

    
    # RUN
  
    async def run(self, message, success_criteria, history):
        state: State = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria or "clear plan",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "plan": None,
            "final_worker_response": None,
        }

        result = await self.graph.ainvoke(
            state,
            config={"configurable": {"thread_id": self.sidekick_id}}
        )

        reply = result.get("final_worker_response", "")

        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply}
        ]

# -----------------------
# UI
# -----------------------
async def setup():
    sk = Sidekick()
    await sk.setup()
    return sk

async def chat(sk, message, success, history):
    return await sk.run(message, success, history), sk

with gr.Blocks() as app:
    sidekick = gr.State()

    chatbot = gr.Chatbot(type="messages")

    message = gr.Textbox(placeholder="Enter your goal")
    success = gr.Textbox(placeholder="Success criteria")

    button = gr.Button("Run")

    app.load(setup, [], sidekick)
    button.click(chat, [sidekick, message, success, chatbot], [chatbot, sidekick])

app.launch(server_name="0.0.0.0", server_port=7860)