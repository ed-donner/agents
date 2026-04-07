import asyncio
import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from sidekick_tools import other_tools, playwright_tools

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a capable assistant with tools: web search, optional browser navigation, Wikipedia, Python (use print() for output), sandbox file I/O, Pushover notifications when asked, direct HTTP fetch for a URL, pretty-print JSON, a running worklog in the sandbox, and a sandbox file listing.

When a request is underspecified (missing output shape, audience, geography, time window, or constraints), ask up to three numbered questions and wait—do not burn search or browser steps until those basics are clear unless the user insists on proceeding.

Keep answers aligned with the success criteria. If you need the user, start with "Question:" and be explicit.

Current local time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success criteria:
{state["success_criteria"]}
"""

        if state.get("feedback_on_work"):
            system_message += f"""

Earlier attempt did not meet the bar. Evaluator feedback:
{state["feedback_on_work"]}
Address this and continue.
"""

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[tool calls]"
                conversation += f"Assistant: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = """You grade whether the assistant finished the job against the stated success criteria.
        Decide if criteria are met and whether the user still owes input."""

        user_message = f"""Conversation:
{self.format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Last assistant message (not counting tool traces):
{last_response}

If the assistant claimed a file was written, trust tool use in the trace when visible; otherwise apply normal skepticism."""

        if state["feedback_on_work"]:
            user_message += f"\nPrior feedback was: {state['feedback_on_work']}\nIf the same failure repeats, mark user_input_needed."

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
                    "content": f"Evaluator Feedback on this answer: {eval_result.feedback}",
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

    async def build_graph(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "worker")
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(
        self,
        user_message: str,
        success_criteria: str,
        history: Optional[List[Any]],
        session_context: str = "",
    ):
        config = {"configurable": {"thread_id": self.sidekick_id}, "recursion_limit": 45}
        model_message = user_message.strip()
        ctx = (session_context or "").strip()
        if ctx:
            model_message = f"[Session context]\n{ctx}\n\n[Request]\n{user_message.strip()}"

        state = {
            "messages": model_message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        history = history or []
        user = {"role": "user", "content": user_message.strip()}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    def cleanup(self):
        if not self.browser:
            return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.browser.close())
            if self.playwright:
                loop.create_task(self.playwright.stop())
        except RuntimeError:
            asyncio.run(self.browser.close())
            if self.playwright:
                asyncio.run(self.playwright.stop())
