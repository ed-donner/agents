import uuid
import asyncio
from typing import Annotated, List, Any, Optional, Dict
from datetime import datetime

from typing_extensions import TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from sidekick_tools import playwright_tools, other_tools

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
        description="True if the assistant has a question, needs clarification, or appears stuck"
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_message = f"""You are a helpful AI sidekick that uses tools to complete tasks.
You keep working until the success criteria are met or you need to ask the user a question.

Your tools:
- Web browsing (Playwright) — navigate, click, scrape pages
- Web search (Serper) — current info, docs, packages
- Wikipedia — background knowledge
- Python REPL — run code; use print() to see output
- File management — read/write files in the sandbox/ directory
- GitHub — search repos, read source files, list issues
- Memory — save and recall facts that persist across sessions
- Push notifications — alert the user when a long task finishes

Current date/time: {now}

Success criteria:
{state["success_criteria"]}

If you have a question for the user, start your reply with "Question:".
If you are done, give the final answer directly — no preamble about what you did.
"""

        if state.get("feedback_on_work"):
            system_message += f"\nYour previous attempt was rejected. Feedback:\n{state['feedback_on_work']}\nAddress this and try again.\n"

        messages = state["messages"]
        found = False
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found = True
        if not found:
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
                conversation += f"Assistant: {message.content or '[Tool use]'}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = "You evaluate whether a task has been completed successfully by an AI assistant."

        user_message = f"""{self.format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Final assistant response:
{last_response}

Has the success criteria been met? Does the assistant have a question or need user input?
If the assistant says it wrote a file or ran code, trust that it did.
"""
        if state["feedback_on_work"]:
            user_message += f"\nPrevious feedback: {state['feedback_on_work']}\nIf the same mistake repeats, set user_input_needed to True."

        eval_result = self.evaluator_llm_with_output.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ])

        return {
            "messages": [{"role": "assistant", "content": f"Evaluator: {eval_result.feedback}"}],
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
        graph_builder.add_edge(START, "worker")
        graph_builder.add_conditional_edges("worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"})
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges("evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END})
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message: str, success_criteria: str, history: list) -> list:
        config = {"configurable": {"thread_id": self.sidekick_id}}
        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer is clear, accurate, and complete.",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
