"""
Lab 3 - Async LangGraph
"""

from typing import Annotated, List, Any, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_sync_playwright_browser
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from IPython.display import Image, display
import gradio as gr
import uuid
from dotenv import load_dotenv
import sys
from pathlib import Path

load_dotenv(override=True)

# Import config from same directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as config_module

class State(BaseModel):
    """
    The state of the graph.
    """
    messages: Annotated[List[Any], add_messages] = Field("The conversation history")
    success_criteria: str = Field("The success criteria for the task.")
    criteria_met: Optional[bool] = Field("Whether the success criteria has been met.")
    feedback_on_work: Optional[str] = Field("The feedback on the work done by the assistant.")

class EvaluatorOutput(BaseModel):
    """
    The evaluator's assesment of the output.
    """
    feedback: str = Field("The feedback on the output.")
    criteria_met: Optional[bool] = Field("Whether the success criteria has been met.")
    need_user_feedback: Optional[bool] = Field("Whether more user context is needed or not.")

class Tools:
    """
    Defines the tools for the entire system. 
    """
    def __init__(self):
        self.tools = None

    def create_tools(self):
        """
        Create the tools for the entire system.
        """
        self.tools = self.create_browser_tool()

    def create_browser_tool(self):
        """
        Create browser tool.
        """
        sync_browser = create_sync_playwright_browser(headless=False)
        toolkit = PlayWrightBrowserToolkit.from_browser(sync_browser=sync_browser)
        return toolkit.get_tools()

class Nodes:
    """
    Defines the functions needed to create nodes.
    """
    def __init__(self):
        self.model = "gpt-4o-mini"
        self.llm = ChatOpenAI(model=self.model)
        self.tools = Tools()
        self.llm_with_tools = None
        self.llm_with_output = None
        self.state = State(messages=[], success_criteria="", criteria_met=False, feedback_on_work=None)
        self.evaluator = EvaluatorOutput(feedback="", criteria_met=False, need_user_feedback=False)
        self.config = config_module
    
    def worker_node(self, state: State) -> State:
        """
        Worker node logic.
        """
        # initialize the llm with tools.
        if self.llm_with_tools is None:
            self.tools.create_tools()
            self.llm_with_tools = self.llm.bind_tools(self.tools.tools)

        try:
            system_message = self.config.WORKER_PROMPT.format(
                success_criteria=state.success_criteria, 
                criteria_met=state.criteria_met, 
                feedback=state.feedback_on_work
            )
            messages = [SystemMessage(content=system_message)] + state.messages
            response = self.llm_with_tools.invoke(messages)
            return State(
                messages=[response],
                success_criteria=state.success_criteria,
                criteria_met=state.criteria_met,
                feedback_on_work=state.feedback_on_work,
            )
        except Exception as e:
            print(f"Error: {e}")
            return State(
                messages= [SystemMessage(content=f"Error: {e}")],
                success_criteria=state.success_criteria,
                criteria_met=False,
                feedback_on_work=f"Error: {e}"
            )
    
    def evaluator_node(self, state: State) -> EvaluatorOutput:
        """
        Evaluator node logic.
        """
        # initialize the llm with output.
        if self.llm_with_output is None:
            self.llm_with_output = self.llm.with_structured_output(EvaluatorOutput)
        try:
            system_message = self.config.EVALUATOR_PROMPT.format(
                success_criteria=state.success_criteria, 
                conversation_history=state.messages, 
                last_response=state.messages[-1], 
                prior_feedback_clause=state.feedback_on_work
            )
            messages = [SystemMessage(content=system_message)] + state.messages
            response = self.llm_with_output.invoke(messages)
            return {
                "feedback_on_work": response.feedback,
                "criteria_met": response.criteria_met,
                "need_user_feedback": response.need_user_feedback,
            }
        except Exception as e:
            print(f"Error in evaluator node: {e}")
            return {
                "feedback_on_work": str(e),
                "criteria_met": False,
                "need_user_feedback": True,
            }
    
    def _worker_router(self, state: State) -> str:
        """
        Router for the worker node - send to tools if tool_calls, else evaluator.
        """
        last_message = state.messages[-1] if state.messages else None
        if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools_node"
        return "evaluator_node"
    
    def _evaluator_router(self, state: dict) -> str:
        """
        Router for the evaluator node.
        """
        criteria_met = state.get("criteria_met", False) if isinstance(state, dict) else getattr(state, "criteria_met", False)
        need_user_feedback = state.get("need_user_feedback", False) if isinstance(state, dict) else getattr(state, "need_user_feedback", False)
        return "END" if (criteria_met or need_user_feedback) else "worker_node"

class GraphBuilder:
    """
    Build the Graph.
    """
    def __init__(self):
        self.nodes = Nodes()
        self.graph = None
        self.memory = MemorySaver()
    
    def build_graph(self):
        """
        Build the graph.
        """
        graph_builder = StateGraph(State)

        # nodes.
        graph_builder.add_node("worker_node", self.nodes.worker_node)
        graph_builder.add_node("evaluator_node", self.nodes.evaluator_node)
        self.nodes.tools.create_tools()
        graph_builder.add_node("tools_node", ToolNode(tools=self.nodes.tools.tools))

        # edges.
        graph_builder.add_edge(START, "worker_node")
        graph_builder.add_conditional_edges("worker_node", self.nodes._worker_router, {"evaluator_node": "evaluator_node", "tools_node": "tools_node"})
        graph_builder.add_edge("tools_node", "worker_node")
        graph_builder.add_conditional_edges("evaluator_node", self.nodes._evaluator_router, {"worker_node": "worker_node", "END": END})
        
        self.graph = graph_builder.compile(checkpointer=self.memory)

    def view_graph(self):
        """
        View the graph in a mermaid diagram.
        """
        try:
            if self.graph is None:
                self.build_graph()
            png_bytes = self.graph.get_graph().draw_mermaid_png()
            if png_bytes:
                display(Image(png_bytes))
        except Exception as e:
            print(f"Error displaying graph: {e}")

class Chat:
    """
    Chat with graph using gradio interface.
    """
    def __init__(self):
        self.builder = GraphBuilder()
        self.builder.build_graph()
        self.graph = self.builder.graph
        self.make_thread_id()
    
    def make_thread_id(self):
        """
        Making random thread id.
        """
        self.thread_id = str(uuid.uuid4())
        return self.thread_id
    
    async def process_message(self, message: str, success_criteria: str, history: str, thread: str):
        """
        Processing a message with State.
        """
        config = {
            "configurable": {"thread_id": thread},
            "recursion_limit": 50,
        }

        state = {
            "messages": message,
            "success_criteria": success_criteria,
            "criteria_met": False,
            "feedback_on_work": None
        }
        result = await self.graph.ainvoke(state, config=config)
        messages = result.get("messages", [])
        last_ai_content = ""
        for m in reversed(messages):
            if isinstance(m, AIMessage) and m.content:
                last_ai_content = m.content if isinstance(m.content, str) else str(m.content)
                break
        feedback_text = result.get("feedback_on_work") or ""
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": last_ai_content}
        feedback = {"role": "assistant", "content": f"Feedback: {feedback_text}"}
        return history + [user, reply, feedback]

    async def reset(self):
        """
        Create new chat.
        """
        self.make_thread_id()
        return "", "", None, self.thread_id
    
    def chat(self):
        """
        Main chat application with gradio application.
        """
        # view the graph.
        self.builder.view_graph()

        # display the chat interface.
        with gr.Blocks(theme=gr.themes.Default(primary_hue="emerald")) as demo:
            gr.Markdown("## Sidekick Personal Co-worker")
            thread = gr.State(self.thread_id)
            
            with gr.Row():
                chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
            with gr.Group():
                with gr.Row():
                    message = gr.Textbox(show_label=False, placeholder="Your request to your sidekick")
                with gr.Row():
                    success_criteria = gr.Textbox(show_label=False, placeholder="What are your success critiera?")
            with gr.Row():
                reset_button = gr.Button("Reset", variant="stop")
                go_button = gr.Button("Go!", variant="primary")
            message.submit(self.process_message, [message, success_criteria, chatbot, thread], [chatbot])
            success_criteria.submit(self.process_message, [message, success_criteria, chatbot, thread], [chatbot])
            go_button.click(self.process_message, [message, success_criteria, chatbot, thread], [chatbot])
            reset_button.click(self.reset, [], [message, success_criteria, chatbot, thread])

        demo.launch()

if __name__ == "__main__":
    chat = Chat()
    chat.chat()